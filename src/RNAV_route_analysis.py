import pandas as pd
import tabula
import json
import numpy as np
import re

import sys

class AIS_Coordinates():
    def __init__(self,string):
        self.coordinates_str = string.split(' ')

    def lat_lon(self):
        for i in range(0,len(self.coordinates_str),2):
            lat_string=self.coordinates_str[i]
            lon_string=self.coordinates_str[i+1]
            #たまにアスタリスクがついているSTNがあるからアスタリスクを取り除く
            lat_string=lat_string.replace('*','')
            lon_string=lon_string.replace('*','')
            #読みだして数値にスペースがある地点があるからスペースをのぞく
            lat_string=lat_string.replace(' ','')
            lon_string=lon_string.replace(' ','')

            lat=float(lat_string[0:2])+ float(lat_string[2:4])/60+ float(lat_string[4:-1])/3600
            lon=float(lon_string[0:3]) + float(lon_string[3:5])/60 + float(lon_string[5:-1])/3600

        return({'lon':lon,'lat':lat})
class Extract_STN():
    def __init__(self,string):
        self.name_original = string

    def name(self):
        name=self.name_original.replace('(continued)','')
        return(name)


if __name__ == '__main__':

    pdf_path='../ENR_20220127.pdf'

    page_list=list(range(229,387,1))

    route_list=[]

    for page in page_list:
        #奇数ページの時
        if(page==229):
            target_area=[104,70.0,842.00,595.0]
            target_area=[104,70.0,842.00,151.0]
        elif(page % 2 ==1):
            target_area=[0,70.5,842.00,595.0]
            target_area=[0,70.5,842.00,151.8]
        else:
            target_area=[0,25.0,842.00,595.0]
            target_area=[0,25.0,842.00,110.3]
    
        #抽出実行
        dfs = tabula.read_pdf(pdf_path,area=target_area, lattice=True,pages = str(page))

        string_list=[]

        for df in dfs:
            if(len(df)!=0):
                for i in range(len(df)):
                    if(str(df.iloc[i][0])!='nan'):
                        cell_str=str(df.iloc[i][0]).replace('\r','@')
                        #ヘッダー的なところとフッター的なところをのぞく
                        if(cell_str!='1' and ('Route designator' in cell_str)!=True and ('DME GAP' in cell_str)!=True and ('Critical DME' in cell_str)!=True):
                            cell_str_list=cell_str.split('@')
                            for i in range(len(cell_str_list)):
                                if  (('RNAV' in cell_str_list[i]!=True)
                                        or ('[VOR' in cell_str_list[i]!=True)
                                        or ('GNSS' in cell_str_list[i]!=True)
                                        or ('RNP10' in cell_str_list[i]!=True)
                                        or ('continued' in cell_str_list[i]!=True)
                                        or (cell_str_list[i]=='')
                                        )!=True:
                                    string_list+=[cell_str_list[i]]

            list_point=0
            print(string_list)
            while(list_point < len(string_list)):
                try:
                    point_latlon=AIS_Coordinates(string_list[list_point+1]).lat_lon()
                    point_name=Extract_STN(string_list[list_point]).name()
                    route_list[-1]=route_list[-1]+[{'point':point_name,'lon':point_latlon['lon'],'lat':point_latlon['lat']}]
                    list_point+=2
                except:
                    data = dict()
                    data['ROUTE_DESIGNATOR']=string_list[list_point]
                    route_list.append([data])
                    list_point+=1
    print(route_list)


#geojsonファイルを作成していく
    i=0
    j=0

    print()
    while(i<len(route_list)):
        print(route_list[i][0]['ROUTE_DESIGNATOR'])
        if('cont' in route_list[i][0]['ROUTE_DESIGNATOR']):
            print(route_list[i][0]['ROUTE_DESIGNATOR'])
            print(route_list[i])
            del route_list[i][0]['ROUTE_DESIGNATOR']
        i+=1
    i=0

    while(i<len(route_list)-1):
        if(route_list[i][0]['ROUTE_DESIGNATOR'] == route_list[i+1][0]['ROUTE_DESIGNATOR']):
            del route_list[i+1][0]
            route_list[i]=route_list[i]+route_list[i+1]
            del route_list[i+1]
            i+=2
        else:
            i+=1

    i=0
    out_geojson=''
    while(i<len(route_list)):
        print(out_geojson)
        route_designator=route_list[i][0]['ROUTE_DESIGNATOR']
        out_geojson=route_list[i][0]['ROUTE_DESIGNATOR']+'.geojson'
        data = dict()
        data['type'] = 'FeatureCollection'
        data['features'] = []
        j=1
        while(j<len(route_list[i])-1):
            data['features'].append({"type": "Feature",
                "properties": {"ROUTE_DESIGNATOR":route_designator},
                    "geometry": {"type": "LineString",
                    "coordinates": [
                         [route_list[i][j]['lon'], route_list[i][j]['lat']],
                         [route_list[i][j+1]['lon'], route_list[i][j+1]['lat']]]
                    }
                }) 
            j+=1
        with open(out_geojson, mode='wt', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        i+=1
