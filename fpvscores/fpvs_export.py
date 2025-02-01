import json
import logging
from data_export import DataExporter
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy import inspect
import re


class FPVSExport():

    def __init__(self,rhapi):
        self.logger = logging.getLogger(__name__)
        self._rhapi = rhapi

    def register_handlers(self,args):
        if 'register_fn' in args:
            for exporter in self.discover():
                args['register_fn'](exporter)


    def discover(self,*args, **kwargs):
        return [
            DataExporter(
                'JSON FPVScores Upload',
                self.write_json,
                self.assemble_fpvscoresUpload
            )
        ]

    def write_json(self,data):
        payload = json.dumps(data, indent='\t', cls=AlchemyEncoder)

        return {
            'data': payload,
            'encoding': 'application/json',
            'ext': 'json'
        }
    
    def assemble_fpvscoresUpload(self,rhapi):
        payload = {}
        payload['import_settings'] = 'upload_FPVScores'
        payload['Pilot'] = self.assemble_pilots_complete(rhapi)
        payload['Heat'] = rhapi.db.heats
        payload['HeatNode'] = self.assemble_heatnodes_complete(rhapi)
        payload['RaceClass'] = rhapi.db.raceclasses
        payload['GlobalSettings'] = rhapi.db.options
        payload['FPVScores_results'] = rhapi.eventresults.results
        return payload
    


    def assemble_pilots_complete(self, rhapi):
        payload = rhapi.db.pilots
        for pilot in payload:
            pilot.fpvsuuid = self.sanitize_input(rhapi.db.pilot_attribute_value(pilot.id, 'fpvs_uuid'))
            pilot.country = self.sanitize_input(rhapi.db.pilot_attribute_value(pilot.id, 'country'))
            self.sanitize_pilot_attributes(pilot)
        return payload


    def assemble_heatnodes_complete(self,rhapi):
        payload = rhapi.db.slots      
        freqs = json.loads(rhapi.race.frequencyset.frequencies)
        
        for slot in payload:
            if slot.node_index is not None and isinstance(slot.node_index, int):
                slot.node_frequency_band = freqs['b'][slot.node_index] if len(freqs['b']) > slot.node_index else ' '
                slot.node_frequency_c = freqs['c'][slot.node_index] if len(freqs['c']) > slot.node_index else ' '
                slot.node_frequency_f = freqs['f'][slot.node_index] if len(freqs['f']) > slot.node_index else ' '
            else:
                slot.node_frequency_band = ' '
                slot.node_frequency_c = ' '
                slot.node_frequency_f = ' '
            
        return payload


    def sanitize_input(self, value):
        if isinstance(value, str):
            original_value = value
            # Verwijder gevaarlijke tekens behalve '#'
            sanitized = re.sub(r"[\"';\-]", "", value)  # Verwijder specifieke gevaarlijke tekens
            sanitized = re.sub(r"[^\w\s\-\#]", "", sanitized)  # Sta #, letters, cijfers, spaties en - toe
            #print(f"Sanitizing input: Original: {original_value}, Sanitized: {sanitized}")
            return sanitized.strip()
        return value
    
    def sanitize_pilot_attributes(self, pilot):
        for key, value in pilot.__dict__.items():
            pilot.__dict__[key] = self.sanitize_input(value)

class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):  #pylint: disable=arguments-differ
        custom_vars = ['fpvsuuid','country','node_frequency_band','node_frequency_c','node_frequency_f', 'display_name']
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            mapped_instance = inspect(obj)
            fields = {}
            for field in dir(obj): 
                if field in [*mapped_instance.attrs.keys(), *custom_vars]:
                    data = obj.__getattribute__(field)
                    if field != 'query' \
                        and field != 'query_class':
                        try:
                            json.dumps(data) # this will fail on non-encodable values, like other classes
                            if field == 'frequencies':
                                fields[field] = json.loads(data)
                            elif field == 'enter_ats' or field == 'exit_ats':
                                fields[field] = json.loads(data)
                            else:
                                fields[field] = data
                        except TypeError:
                            fields[field] = None

            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)


    