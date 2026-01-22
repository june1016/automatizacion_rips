/**
 * Sistema de Loading Overlay - Optimizado con MutationObserver
 * Controla spinner global durante carga inicial y Paso 3
 */

(function() {
    'use strict';
    
    // ============================================
    // CONFIGURACIÓN
    // ============================================
    
    const CONFIG = {
        INITIAL_HIDE_DELAY: 1500,      // Delay inicial al cargar app
        MIN_LOADING_TIME: 800,          // Tiempo mínimo visible en Paso 3
        MAX_LOADING_TIME: 3000,         // Timeout máximo si algo falla
        TRANSITION_DURATION: 600        // Duración de transición CSS
    };
    
    // ============================================
    // VARIABLES GLOBALES
    // ============================================
    
    let loadingOverlay = null;
    let loadingStartTime = null;
    let loadingTimeout = null;
    let observer = null;
    let panelsDetected = {
        filtrosGlobales: false,
        filtrosEspecificos: false,
        columnas: false
    };
    
    // ============================================
    // FUNCIONES PRINCIPALES
    // ============================================
    
    /**
     * Mostrar loading overlay
     */
    function showLoading() {
        if (!loadingOverlay) return;
        
        loadingOverlay.classList.remove('loaded');
        loadingOverlay.style.display = 'flex';
        // console.log('✅ Loading mostrado');
    }
    
    /**
     * Ocultar loading overlay
     */
    function hideLoading() {
        if (!loadingOverlay) return;
        
        loadingOverlay.classList.add('loaded');
        
        // Esperar a que termine la transición CSS antes de ocultar
        setTimeout(function() {
            loadingOverlay.style.display = 'none';
        }, CONFIG.TRANSITION_DURATION);
        
        // console.log('✅ Loading ocultado');
    }
    
    /**
     * Verificar si todos los paneles críticos están listos
     */
    function arePanelsReady() {
        const mainContent = document.getElementById('main-content');
        if (!mainContent) return false;
        
        // Verificar que los 3 paneles principales existan y tengan contenido
        const filtrosGlobales = document.getElementById('panel-filtros-globales');
        const filtrosEspecificos = document.getElementById('panel-filtros-especificos');
        const columnas = document.getElementById('panel-columnas');
        
        const globalesReady = filtrosGlobales && filtrosGlobales.children.length > 0;
        const especificosReady = filtrosEspecificos && filtrosEspecificos.children.length > 0;
        const columnasReady = columnas && columnas.children.length > 0;
        
        return globalesReady && especificosReady && columnasReady;
    }
    
    /**
     * Intentar ocultar loading si las condiciones se cumplen
     */
    function tryHideLoading() {
        if (!loadingStartTime) return;
        
        const elapsedTime = Date.now() - loadingStartTime;
        const panelsReady = arePanelsReady();
        
        // console.log('⏱️ Verificando condiciones:', {
        //     elapsedTime: elapsedTime + 'ms',
        //     minTimePassed: elapsedTime >= CONFIG.MIN_LOADING_TIME,
        //     panelsReady: panelsReady
        // });
        
        // Condiciones para ocultar:
        // 1. Han pasado al menos MIN_LOADING_TIME
        // 2. Todos los paneles están listos
        if (elapsedTime >= CONFIG.MIN_LOADING_TIME && panelsReady) {
            // console.log('✅ Condiciones cumplidas - Ocultando loading');
            hideLoading();
            loadingStartTime = null;
            
            // Detener observer
            if (observer) {
                observer.disconnect();
            }
            
            return true;
        }
        
        return false;
    }
    
    /**
     * Mostrar loading específico para Paso 3
     */
    function showForStep3() {
        //  console.log('🚀 Iniciando loading para Paso 3');

        // Si overlay no existe, buscarlo ahora
        if (!loadingOverlay) {
            console.log('⚠️ Overlay no existe, buscando...');
            findLoadingOverlay(function() {
                showForStep3(); // Reintentar mostrar después de encontrar
            });
            return;
        }   
        
        // Resetear estado de paneles
        panelsDetected = {
            filtrosGlobales: false,
            filtrosEspecificos: false,
            columnas: false
        };
        
        // Mostrar loading
        showLoading();
        loadingStartTime = Date.now();
        
        // Limpiar timeout anterior
        if (loadingTimeout) {
            clearTimeout(loadingTimeout);
        }
        
        // Timeout de seguridad - ocultar después de MAX_LOADING_TIME
        loadingTimeout = setTimeout(function() {
            if (loadingStartTime) {
                console.warn('⚠️ Timeout alcanzado - Ocultando loading forzado');
                hideLoading();
                loadingStartTime = null;
            }
        }, CONFIG.MAX_LOADING_TIME);
        
        // Iniciar observación del DOM
        startObserving();
        
        // Verificar cada 100ms si los paneles están listos
        const checkInterval = setInterval(function() {
            if (tryHideLoading()) {
                clearInterval(checkInterval);
            }
        }, 100);
        
        // Limpiar intervalo después de timeout máximo
        setTimeout(function() {
            clearInterval(checkInterval);
        }, CONFIG.MAX_LOADING_TIME);
    }
    
    /**
     * Iniciar observación del DOM para detectar paneles
     */
    function startObserving() {
        const mainContent = document.getElementById('main-content');
        if (!mainContent) {
            console.warn('⚠️ main-content no encontrado');
            return;
        }
        
        // Crear observer si no existe
        if (!observer) {
            observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    // Solo procesar nodos agregados
                    if (mutation.addedNodes.length > 0) {
                        mutation.addedNodes.forEach(function(node) {
                            if (node.nodeType === 1) { // Element node
                                checkForPanels(node);
                            }
                        });
                    }
                });
                
                // Después de cada mutación, verificar si podemos ocultar
                tryHideLoading();
            });
        }
        
        // Observar cambios en main-content
        observer.observe(mainContent, {
            childList: true,
            subtree: true
        });
        
        // console.log('👁️ Observer iniciado');
    }
    
    /**
     * Verificar si un nodo contiene alguno de los paneles críticos
     */
    function checkForPanels(node) {
        // Verificar si el nodo es uno de los paneles o lo contiene
        if (node.id === 'panel-filtros-globales' || node.querySelector('#panel-filtros-globales')) {
            panelsDetected.filtrosGlobales = true;
            // console.log('✓ Panel filtros globales detectado');
        }
        
        if (node.id === 'panel-filtros-especificos' || node.querySelector('#panel-filtros-especificos')) {
            panelsDetected.filtrosEspecificos = true;
            // console.log('✓ Panel filtros específicos detectado');
        }
        
        if (node.id === 'panel-columnas' || node.querySelector('#panel-columnas')) {
            panelsDetected.columnas = true;
            // console.log('✓ Panel columnas detectado');
        }
    }
    
    // ============================================
    // INICIALIZACIÓN CON REINTENTOS
    // ============================================

    /**
     * Buscar loading overlay con reintentos
     */
    function findLoadingOverlay(callback, attempts = 0) {
        const overlay = document.querySelector('.global-loading-overlay');
        
        if (overlay) {
            // console.log('✅ Loading overlay encontrado');
            loadingOverlay = overlay;
            if (callback) callback();
            return true;
        }
        
        if (attempts < 20) { // Máximo 20 intentos (2 segundos)
            //console.log('⏳ Loading overlay no encontrado, reintentando... (' + (attempts + 1) + '/20)');
            setTimeout(function() {
                findLoadingOverlay(callback, attempts + 1);
            }, 100);
            return false;
        }
        
        console.error('❌ Loading overlay no encontrado después de 20 intentos');
        return false;
    }

    /**
     * Inicializar al cargar DOM
     */
    function init() {
        // console.log('🚀 Inicializando sistema de loading...');
        
        // Buscar overlay con reintentos
        findLoadingOverlay(function() {
            // Ocultar loading inicial después de delay
            setTimeout(function() {
                if (!loadingStartTime) { // Solo si no estamos en Paso 3
                    hideLoading();
                    // console.log('✅ Loading inicial ocultado');
                }
            }, CONFIG.INITIAL_HIDE_DELAY);
            
            //console.log('✅ Sistema de loading inicializado');
        });
    }

    // Inicializar cuando DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // ============================================
    // API PÚBLICA
    // ============================================
    
    window.dashLoadingSystem = {
        show: showLoading,
        hide: hideLoading,
        showForStep3: showForStep3,
        arePanelsReady: arePanelsReady,
        config: CONFIG
    };
    
    // console.log('📦 dashLoadingSystem cargado');
    
})();