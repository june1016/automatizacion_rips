# Sistema de pool de Conexiones

## Problema resuelto:

### ANTES (Sin Pool Optimizado):

**Cada query:**
1. Crear conexión TCP → 50-100ms
2. Autenticar con BD → 30-50ms
3. Ejecutar query → Xs
4. Cerrar conexión → 20-30ms

Total overhead: ~100-180ms POR QUERY

**Con 10 usuarios simultáneos:**

10 conexiones abiertas/cerradas constantemente
Overhead acumulado: ~1-1.8 segundos desperdiciados
BD procesa 10 handshakes innecesarios

## DESPUÉS (Con Pool Optimizado):

**Conexiones pre-creadas y reutilizadas:**
1. Tomar conexión del pool → 1-5ms
2. Ejecutar query → Xs
3. Devolver al pool → 1-5ms

Total overhead: ~2-10ms POR QUERY

**Con 10 usuarios simultáneos:**
- Reutilización de 10-15 conexiones del pool
- Overhead mínimo: ~20-100ms total
- **Mejora: 90-95% reducción en overhead**

---

## Explicación del Sistema de Pool

### Concepto Simple:

**Sin Pool = Taxi tradicional:**
```
Usuario necesita ir al mall
  ↓
Llama taxi (espera 5 min)
  ↓
Taxi llega y lo lleva
  ↓
Usuario baja, taxi se va
  ↓
Siguiente usuario llama taxi (espera 5 min otra vez)
```

**Con Pool = Uber en zona de alta demanda:**
```
App pre-posiciona 15 taxis en la zona
  ↓
Usuario pide viaje → Taxi disponible inmediatamente
  ↓
Usuario baja → Taxi vuelve a la zona (no se va a casa)
  ↓
Siguiente usuario → Mismo taxi reutilizado inmediatamente
```

**Ejemplo con Conexión 67 (Principal):**

```
Estado Normal:
┌─────────────────────────────────────┐
│ Pool de 15 conexiones permanentes   │
│ [●][●][●][●][●][●][●][●][●][●]      │ ← 15 conexiones activas
│ [●][●][●][●][●]                     │
│                                     │
│ Overflow: 0/25 (reserva sin usar)   │
└─────────────────────────────────────┘

Usuario 1 ejecuta query:
┌─────────────────────────────────────┐
│ [◉][●][●][●][●][●][●][●][●][●]      │ ← Usa conexión #1
│ [●][●][●][●][●]                     │
│ checked_out: 1                      │
└─────────────────────────────────────┘

10 usuarios ejecutan queries:
┌─────────────────────────────────────┐
│ [◉][◉][◉][◉][◉][◉][◉][◉][◉][◉] │ ← 10 en uso
│ [●][●][●][●][●]                     │    5 libres
│ checked_out: 10, overflow: 0        │
└─────────────────────────────────────┘

20 usuarios ejecutan queries (pico):
┌─────────────────────────────────────┐
│ [◉][◉][◉][◉][◉][◉][◉][◉][◉][◉] │ ← 15 base usadas
│ [◉][◉][◉][◉][◉]                  │
│                                     │
│ Overflow: [◉][◉][◉][◉][◉]        │ ← 5 extra creadas
│ checked_out: 15, overflow: 5        │
└─────────────────────────────────────┘

Usuario 21 intenta query (pool lleno):
┌─────────────────────────────────────┐
│ Pool: 15/15 usadas                  │
│ Overflow: 25/25 usadas              │
│                                     │
│ Usuario 21: ESPERA hasta 30s        │ ← pool_timeout
│ (Si alguien termina → toma esa)     │
└─────────────────────────────────────┘
```
Total sistema: 42 base + 70 overflow = 112 conexiones máx

---

### Componentes del Pool:

```
pool_size = 15              # "Taxis base" siempre disponibles
max_overflow = 25           # "Taxis extra" si hay pico de demanda
pool_timeout = 30           # Tiempo máximo de espera si todos ocupados
pool_recycle = 3600         # Renovar taxis cada hora (evitar problemas)
pool_pre_ping = True        # Verificar taxi funciona antes de asignar
```

- Ver config/settings.py → PoolSettings
- Valores ajustados según uso esperado de cada BD
- 
## Monitoreo
python -c "from config import db_connections; print(db_connections.get_pool_status())"

## ¿Cuándo ajustar?
Si ves errores "pool timeout" o "too many connections"
→ Aumentar pool_size o max_overflow


