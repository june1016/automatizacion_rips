"""Testing de pools de conexiones bajo carga."""
import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import text
from config.database import db_connections

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def execute_test_query(connection_id: str, query_id: int):
    """Ejecuta query de prueba y retorna timing."""
    start = time.time()
    
    try:
        session = db_connections.get_session(connection_id)
        
        # Query adaptada según motor de BD
        if connection_id == '38':  # PostgreSQL
            query = "SELECT pg_sleep(1), :query_id"
        else:  # MySQL (67, 39, 82)
            query = "SELECT SLEEP(1), :query_id"
        
        result = session.execute(text(query), {'query_id': query_id})
        result.fetchall()
        session.close()
        
        elapsed = time.time() - start
        logger.info(f"✓ Query {query_id} en conn {connection_id}: {elapsed:.2f}s")
        return True, elapsed
        
    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"✗ Query {query_id} falló: {str(e)}")
        return False, elapsed

def test_single_connection():
    """Test 1: Una conexión simple."""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Conexión Simple")
    logger.info("="*60)
    
    success, elapsed = execute_test_query('67', 1)
    assert success, "Query falló"
    assert elapsed < 2, f"Query muy lenta: {elapsed}s"
    
    logger.info("✅ Test 1 PASÓ\n")


def test_concurrent_within_pool():
    """Test 2: 10 conexiones concurrentes (dentro de pool size=15)."""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: 10 Conexiones Concurrentes (Dentro de Pool)")
    logger.info("="*60)
    
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(execute_test_query, '67', i)
            for i in range(1, 11)
        ]
        
        results = [f.result() for f in as_completed(futures)]
    
    total_time = time.time() - start
    success_count = sum(1 for r in results if r[0])
    
    logger.info(f"Completadas: {success_count}/10")
    logger.info(f"Tiempo total: {total_time:.2f}s")
    
    # Deben ejecutarse en paralelo (~1s), no secuencial (~10s)
    assert total_time < 3, f"Queries no en paralelo: {total_time}s"
    assert success_count == 10, f"Solo {success_count}/10 exitosas"
    
    logger.info("✅ Test 2 PASÓ\n")


def test_overflow():
    """Test 3: 20 conexiones (activa overflow: 15 base + 5 overflow)."""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: 20 Conexiones (Activando Overflow)")
    logger.info("="*60)
    
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(execute_test_query, '67', i)
            for i in range(1, 21)
        ]
        
        results = [f.result() for f in as_completed(futures)]
    
    total_time = time.time() - start
    success_count = sum(1 for r in results if r[0])
    
    logger.info(f"Completadas: {success_count}/20")
    logger.info(f"Tiempo total: {total_time:.2f}s")
    
    assert total_time < 4, f"Overflow no funcionó: {total_time}s"
    assert success_count == 20, f"Solo {success_count}/20 exitosas"
    
    logger.info("✅ Test 3 PASÓ\n")


def test_pool_status_under_load():
    """Test 4: Verificar stats de pool bajo carga."""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: Stats de Pool Bajo Carga")
    logger.info("="*60)
    
    # Estado inicial
    status_before = db_connections.get_pool_status('67')
    logger.info(f"Antes: {status_before}")
    
    # Lanzar 5 queries y verificar inmediatamente
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(execute_test_query, '67', i)
            for i in range(1, 6)
        ]
        
        # Verificar stats mientras queries están ejecutándose
        time.sleep(0.5)  # Dar tiempo a que inicien
        status_during = db_connections.get_pool_status('67')
        logger.info(f"Durante: {status_during}")
        
        # Esperar a que terminen
        [f.result() for f in as_completed(futures)]
    
    # Estado final
    status_after = db_connections.get_pool_status('67')
    logger.info(f"Después: {status_after}")
    
    # Verificar que checked_out aumentó durante ejecución
    assert status_during['checked_out'] > 0, "No detectó conexiones activas"
    assert status_after['checked_out'] == 0, "Conexiones no liberadas"
    
    logger.info("✅ Test 4 PASÓ\n")


def test_multiple_connections():
    """Test 5: Usar las 4 conexiones simultáneamente."""
    logger.info("\n" + "="*60)
    logger.info("TEST 5: 4 Conexiones Simultáneas")
    logger.info("="*60)
    
    connections = ['67', '38', '39', '82']
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(execute_test_query, conn_id, i)
            for i, conn_id in enumerate(connections, 1)
        ]
        
        results = [f.result() for f in as_completed(futures)]
    
    success_count = sum(1 for r in results if r[0])
    
    logger.info(f"Completadas: {success_count}/4")
    assert success_count == 4, f"Solo {success_count}/4 exitosas"
    
    logger.info("✅ Test 5 PASÓ\n")


if __name__ == '__main__':
    logger.info("\n" + "="*60)
    logger.info("INICIANDO SUITE DE TESTS DE POOL")
    logger.info("="*60)
    
    try:
        test_single_connection()
        test_concurrent_within_pool()
        test_overflow()
        test_pool_status_under_load()
        test_multiple_connections()
        
        logger.info("\n" + "="*60)
        logger.info("🎉 TODOS LOS TESTS PASARON")
        logger.info("="*60)
        
    except AssertionError as e:
        logger.error(f"\n❌ TEST FALLÓ: {e}")
    except Exception as e:
        logger.error(f"\n💥 ERROR: {e}")