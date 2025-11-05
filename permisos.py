import sqlite3
import os
import sys
DB_NAME = "database.db"

def obtener_permisos_por_rol(rol):
    """
    Obtiene los permisos para un rol específico.
    Retorna un diccionario con módulo como clave y acceso (True/False) como valor.
    """
    if rol == "Administrador":
        return {
            "Ventas": True,
            "Inventario": True,
            "Clientes": True,
            "Reportes": True,
            "Configuracion": True,
            "Usuarios": True
        }
    elif rol == "Cajero":
        return {
            "Ventas": True,
            "Inventario": True,
            "Clientes": True,
            "Reportes": False,
            "Configuracion": False,
            "Usuarios": False
        }
    return {}  # Return empty permissions for unknown roles

def tiene_acceso(rol, modulo):
    """
    Verifica si un rol tiene acceso a un módulo específico.
    """
    permisos = obtener_permisos_por_rol(rol)
    return permisos.get(modulo, False)
