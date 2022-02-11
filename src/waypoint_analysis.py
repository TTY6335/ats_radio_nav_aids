import pandas as pd
import tabula
import json

import sys

class AIS_Coordinates():
    def __init__(self,string):
        self.coordinates_str = string
        try:
            self.lat_string,self.lon_string=self.coordinates_str.replace('\r',',').split(',')
        except:
            print('err in coordinates')
            pass

    def lat(self):
        return (float(self.lat_string[0:2]) + float(self.lat_string[2:4])/60 + float(self.lat_string[4:-1])/3600)

    def lon(self):
        return (float(self.lon_string[0:3]) + float(self.lon_string[3:5])/60 + float(self.lon_string[5:-1])/3600)

class Name_code():
    def __init__(self,string):
        self.name_str = string
        try:
            replace_str=string.replace('\r',',').replace(' ','')
        except:
#            print('err in init1' + str(self.name_str))
            pass

        try:
            self.name_en,self.name_jp=replace_str.split(',')
        except:
            if(str(self.name_str) !='nan'):
                print('err in  '+str(self.name_str.replace('\r',',')))
            pass

    def name(self):
        try:
            return({"Name-code designator":{"en": self.name_en, "ja":self.name_jp}})
        except:
            return({"Name-code designator":{"en": "None", "ja":"None"}})

if __name__ == '__main__':



    pdf_path='ENR_20220127.pdf'
    out_geojson='waypoint.geojson'

    odd_pages=list(range(519,626,2))
    dfs = tabula.read_pdf(pdf_path,area=[0,70.0,842.00,595.0], lattice=True,pages = odd_pages)

    data = dict()
    data['type'] = 'FeatureCollection'
    data['features'] = []

    for df in dfs:
        column=df.columns[0].replace('\r','')
        if(column=='識別Name-code designator'):
            for i in range (df.index.stop):
                if(str(df.loc[i][1])!='nan'):
                    name_obj=Name_code(df.loc[i][1])
                    name_dict=name_obj.name()

                    if(name_dict['Name-code designator']['en'] != 'None'):
                        coordinates_obj=AIS_Coordinates(df.loc[i][2])
                        data['features'].append({'type': 'Feature',
                              'properties': {
                                    'Name-code designator':
                                    {'en':name_dict["Name-code designator"]["en"], 'ja':name_dict["Name-code designator"]["ja"] }
                                  },
                              'geometry': {'type': 'Point','coordinates': [coordinates_obj.lon(),coordinates_obj.lat()]}
                              })

    even_pages=list(range(520,626,2))
    dfs = tabula.read_pdf(pdf_path,area=[0,27.5,842.00,595.0], lattice=True,pages = even_pages)

    for df in dfs:
        column=df.columns[0].replace('\r','')
        if(column=='識別Name-code designator'):
            for i in range (df.index.stop):
                if(str(df.loc[i][1])!='nan'):
                    name_obj=Name_code(df.loc[i][1])
                    name_dict=name_obj.name()

                    if(name_dict['Name-code designator']['en'] != 'None'):
                        coordinates_obj=AIS_Coordinates(df.loc[i][2])
                        data['features'].append({'type': 'Feature',
                              'properties': {
                                    'Name-code designator':
                                    {'en':name_dict["Name-code designator"]["en"], 'ja':name_dict["Name-code designator"]["ja"] }
                                  },
                              'geometry': {'type': 'Point','coordinates': [coordinates_obj.lon(),coordinates_obj.lat()]}
                              })



    # 辞書オブジェクトをJSONファイルへ出力
    with open(out_geojson, mode='wt', encoding='utf-8') as file:
      json.dump(data, file, ensure_ascii=False, indent=2)

