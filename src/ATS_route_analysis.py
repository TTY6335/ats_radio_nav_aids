import pandas as pd
import tabula
import json
import numpy as np

import sys

class AIS_Coordinates():
    def __init__(self,string):
        self.coordinates_str = string.split('/')

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
        name=self.name_original.replace('(Cont\'d) ','')
        return(name)


if __name__ == '__main__':

    pdf_path='../ENR_20220127.pdf'

    page_list=list(range(209,226,1))
#    page_list=list(range(208,209,1))
    route_list=[]

    for page in page_list:
        #奇数ページの時
        if(page==165):
            target_area=[260,70.0,842.00,595.0]
        elif(page % 2 ==1):
            target_area=[0,70.5,842.00,595.0]
#            target_area=[0,70.95,842.00,188.5]
        else:
            target_area=[0,25.0,842.00,595.0]
            target_area=[0,28.0,842.00,595.0]
    
        #抽出実行
        dfs = tabula.read_pdf(pdf_path,area=target_area, lattice=True,pages = str(page))

        string_list=[]

        for df in dfs:
            if(len(df)!=0):
                for i in range(len(df)):
                    if(str(df.iloc[i][0])!='nan'):
                        cell_str_list=str(df.iloc[i][0]).split('\r')
                        #ヘッダー的なところをのぞく
                        if(cell_str_list[0]!='1'):
                            point_cood=cell_str_list[0]
                            string_list=string_list+[point_cood]
                            point_name=' '.join(cell_str_list[1:])
                            if(point_name!=''):
                                string_list=string_list+[point_name]

            list_point=0
            point_latlon={'lon':np.nan,'lat':np.nan}

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
        print(string_list)


#geojsonファイルを作成していく
    i=0
    j=0

    j=1
    print()
    while(i<len(route_list)):
#        if(route_list[i][0]['ROUTE_DESIGNATOR'] =='(Cont\'d)'):
        if('Cont' in route_list[i][0]['ROUTE_DESIGNATOR']):
            del route_list[i]
        i+=1
    i=0
    print(route_list)
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
        print(route_list[i])
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
