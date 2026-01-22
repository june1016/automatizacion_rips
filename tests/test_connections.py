"""Script de prueba de conexiones a bases de datos."""
import sys
from pathlib import Path

# Agregar ruta del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import db_connections
from sqlalchemy import text


def test_connection(conn_id: str, conn_name: str) -> bool:
    """Prueba conexión a base de datos específica."""
    try:
        session = db_connections.get_session(conn_id)
        
        # Query de prueba según motor
        if conn_id == '38':
            result = session.execute(text("SELECT 1 as test"))
        else:
            result = session.execute(text("SELECT 1 as test"))
        
        row = result.fetchone()
        session.close()
        
        if row and row[0] == 1:
            print(f"✅ Conexión {conn_id} ({conn_name}): OK")
            return True
        else:
            print(f"❌ Conexión {conn_id} ({conn_name}): Query falló")
            return False
            
    except Exception as e:
        print(f"❌ Conexión {conn_id} ({conn_name}): ERROR - {str(e)}")
        return False


def main():
    """Ejecuta prueba de todas las conexiones."""
    print("\n=== Prueba de Conexiones RIPS ===\n")
    
    connections = [
        ('67', 'MySQL - system_savia (espejo)'),
        ('38', 'PostgreSQL - db_savia_b'),
        ('39', 'MySQL - ODS_SAVIA'),
        ('82', 'MySQL - gestion_dato')
    ]
    
    results = []
    for conn_id, conn_name in connections:
        results.append(test_connection(conn_id, conn_name))
    
    print("\n=== Resumen ===")
    total = len(results)
    success = sum(results)
    print(f"Exitosas: {success}/{total}")
    
    if success == total:
        print("\n✅ Todas las conexiones OK. Listo para desarrollo.\n")
        return 0
    else:
        print("\n⚠️  Algunas conexiones fallaron. Revisar credenciales en .env\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())