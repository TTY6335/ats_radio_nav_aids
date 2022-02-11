import pandas as pd
import tabula
import json
import numpy as np

import sys

class AIS_Coordinates():
    def __init__(self,string):
        self.coordinates_str = string.split('\r')

    def lat_lon(self):
        position_list=[]
        for i in range(0,len(self.coordinates_str),2):
            lat_string=self.coordinates_str[i]
            lon_string=self.coordinates_str[i+1]
            #たまにアスタリスクがついているSTNがあるからアスタリスクを取り除く
            lat_string=lat_string.replace('*','')
            lon_string=lon_string.replace('*','')

            lat=float(lat_string[0:2])+ float(lat_string[2:4])/60+ float(lat_string[4:-1])/3600
            lon=float(lon_string[0:3]) + float(lon_string[3:5])/60 + float(lon_string[5:-1])/3600
            position_list.append([lon,lat])

        return(position_list)

class Extract_STN():
    def __init__(self,string):
        self.name_part_list = string.split('\r')

    def name(self):
        #かっこがある文字列をリストから消去
        #最初の日本語のSTNはリストから消去
        l_in_not = [s for s in self.name_part_list[1:] if '(' not in s]
        l_in_not = [s for s in l_in_not if len(s)!=0]
        stn_list=[]
        for i in range(0,len(l_in_not),2):
            stn_list.append(l_in_not[i]+' '+l_in_not[i+1])
        
        return(stn_list)

class Extract_ELV():
    def __init__(self,string):
        self.elev_part_list = str(string).split('\r')

    def elev_list(self):
        elev_list=[{'m':np.nan,'ft':np.nan}]
        #nanだったらnanに変更
        if(self.elev_part_list[0]=='nan'):
            elev_list[0]={'m':np.nan,'ft':np.nan}
        else:
            for elev in self.elev_part_list:
                if('m' in elev):
                #mの標高
                    elev=elev.replace(' ','')
                    elev=elev.replace('m','')
                    elev_list[0]['m']=float(elev)
                else:
                 #ftの標高
                    elev=elev.replace(' ','')
                    elev=elev.replace('(','')
                    elev=elev.replace(')','')
                    elev=elev.replace('ft','')
                    elev_list[0]['ft']=float(elev)
        return(elev_list)

if __name__ == '__main__':

    pdf_path='../ENR_20220127.pdf'
    out_geojson='navaid.geojson'

    dfs = tabula.read_pdf(pdf_path, lattice=True,pages = '493-515')

    data = dict()
    data['type'] = 'FeatureCollection'
    data['features'] = []

    for df in dfs:
        if(len(df)!=0):
            for i in range(len(df)):
                if(len(df.iloc[i][0].split('\r'))>1):
                    stn_list=Extract_STN(df.iloc[i][0]).name()
                    id_list=df.iloc[i][1].split('\r')
                    elev_list=Extract_ELV(df.iloc[i][5]).elev_list()
                    cood_list=AIS_Coordinates(df.iloc[i][4]).lat_lon()

                    for i in range(len(stn_list)):
                        data['features'].append({'type': 'Feature',
                              'properties': {
                                    'STN':stn_list[i],
                                    'ID':id_list[i],
                                    'ELEV':{'m':elev_list[0]['m'],'ft':elev_list[0]['ft']}
                                  },
                              'geometry': {'type': 'Point','coordinates': [cood_list[i][0],cood_list[i][1]]}
                              })
    # 辞書オブジェクトをJSONファイルへ出力
    with open(out_geojson, mode='wt', encoding='utf-8') as file:
      json.dump(data, file, ensure_ascii=False, indent=2)
