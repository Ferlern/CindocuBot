from .data_controller.models import Codes


def get_all():
    return Codes.select().dicts().execute()


def get_saved_codes(name: str):
    return Codes.select().where((Codes.group == name) | (Codes.name == name)).dicts().execute()


def save_code(code, name):
    isinstance = Codes.get_or_create(name=name)[0]
    isinstance.code = code
    isinstance.save()
    
    
def delete_codes(name: str):
    Codes.delete().where((Codes.group == name) | (Codes.name == name)).execute()
    

def change_name(old_name: str, new_name: str):
    Codes.update({Codes.name: new_name}).where(Codes.name == old_name).execute()
   
    
def change_group(name: str, new_group: str):
    Codes.update({Codes.group: new_group}).where(Codes.name == name).execute()