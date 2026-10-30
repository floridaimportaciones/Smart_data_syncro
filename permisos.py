from Smart_data_syncro.services.permiso_service import PermisoService

_service = PermisoService()


def obtener_permisos_por_rol(rol):
    """
    Obtiene los permisos para un rol específico, leidos de la tabla permisos.
    Retorna un diccionario con módulo como clave y acceso (True/False) como valor.
    """
    return _service.obtener_permisos_por_rol(rol)


def tiene_acceso(rol, modulo):
    """
    Verifica si un rol tiene acceso a un módulo específico.
    """
    return _service.tiene_acceso(rol, modulo)
