#!/usr/bin/env python3
"""
logger.py - Capturador de logs para aplicaciones Python
Versión corregida - Maneja codificaciones de Windows
"""

import os
import sys
import locale
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple
import subprocess

class LogManager:
    """Gestor centralizado para captura y organización de logs"""
    
    LOGS_DIR = "logs"
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, app_name: Optional[str] = None):
        self.app_name = app_name or "app"
        self.logs_dir = Path(self.LOGS_DIR)
        self._setup_directories()
        
    def _setup_directories(self):
        """Crea la estructura de directorios para logs"""
        self.logs_dir.mkdir(exist_ok=True)
        self.today_dir = self.logs_dir / datetime.now().strftime("%Y-%m-%d")
        self.today_dir.mkdir(exist_ok=True)
        
    def get_log_filename(self, suffix: str = "") -> str:
        """Genera nombre de archivo de log con timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix_str = f"_{suffix}" if suffix else ""
        return str(self.today_dir / f"{self.app_name}{suffix_str}_{timestamp}.log")

class ConsoleCapture:
    """Captura en tiempo real de salida de consola"""
    
    def __init__(self, log_manager: LogManager):
        self.log_manager = log_manager
        
    def _get_system_encoding(self) -> Tuple[str, str]:
        """
        Detecta la codificación del sistema.
        Returns: (codificación_entrada, codificación_salida)
        """
        try:
            # Para Windows
            import ctypes
            kernel32 = ctypes.windll.kernel32
            codepage = kernel32.GetConsoleCP()
            
            # Mapeo de code pages a Python encodings
            cp_to_encoding = {
                65001: 'utf-8',      # UTF-8
                1252: 'cp1252',      # Windows Latin-1 (Europa Occidental)
                1251: 'cp1251',      # Windows Cyrillic
                932: 'cp932',        # Japanese Shift-JIS
                949: 'cp949',        # Korean
                936: 'gbk',          # Chinese Simplified
                950: 'big5',         # Chinese Traditional
            }
            
            encoding = cp_to_encoding.get(codepage, 'cp1252')
            return (encoding, encoding)
            
        except (AttributeError, ImportError):
            # Para Linux/Mac o si falla en Windows
            return (locale.getpreferredencoding(), locale.getpreferredencoding())
    
    def _safe_decode(self, data: bytes, encoding: str) -> str:
        """Decodifica bytes a string manejando errores de codificación"""
        try:
            return data.decode(encoding, errors='strict')
        except UnicodeDecodeError:
            # Si falla, intenta con reemplazo de caracteres inválidos
            return data.decode(encoding, errors='replace')
    
    def run_application(self, command: List[str], log_suffix: str = "") -> int:
        """
        Ejecuta una aplicación capturando toda su salida.
        
        Args:
            command: Comando y argumentos a ejecutar
            log_suffix: Sufijo para el archivo de log
            
        Returns:
            Código de salida de la aplicación
        """
        log_filename = self.log_manager.get_log_filename(log_suffix)
        
        print(f"🚀 Ejecutando: {' '.join(command)}")
        print(f"📁 Logs en: {log_filename}")
        print("🛑 Presiona Ctrl+C para detener\n")
        
        # Detectar codificación del sistema
        input_encoding, output_encoding = self._get_system_encoding()
        print(f"🔤 Codificación detectada: {input_encoding}")
        
        try:
            with open(log_filename, 'a', encoding=output_encoding, errors='replace') as log_file:
                # Escribir cabecera
                log_file.write(f"{'='*60}\n")
                log_file.write(f"Inicio: {datetime.now()}\n")
                log_file.write(f"Comando: {' '.join(command)}\n")
                log_file.write(f"Codificación: {input_encoding}\n")
                log_file.write(f"{'='*60}\n\n")
                log_file.flush()
                
                # Configurar proceso - SIN especificar encoding
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    bufsize=1
                )
                
                # Variable para controlar el hilo
                stop_thread = threading.Event()
                
                def read_output():
                    """Hilo para leer y procesar la salida del proceso"""
                    while not stop_thread.is_set():
                        # Leer bytes del proceso
                        output = process.stdout.readline()
                        if output:
                            try:
                                # Decodificar usando la codificación detectada
                                line = self._safe_decode(output, input_encoding)
                                
                                # Mostrar en consola
                                sys.stdout.write(line)
                                sys.stdout.flush()
                                
                                # Guardar en archivo
                                log_file.write(line)
                                log_file.flush()
                            except Exception as e:
                                # En caso de error, guardar los bytes crudos
                                log_file.write(f"[ERROR DECODIFICACIÓN: {e}]\n")
                                log_file.write(f"[BYTES CRUDOS: {output.hex()}]\n")
                        elif process.poll() is not None:
                            # El proceso terminó
                            break
                
                # Iniciar hilo
                reader_thread = threading.Thread(target=read_output)
                reader_thread.daemon = True
                reader_thread.start()
                
                try:
                    # Esperar a que el proceso termine
                    process.wait()
                    
                    # Dar tiempo para leer salida restante
                    stop_thread.set()
                    reader_thread.join(timeout=2)
                    
                except KeyboardInterrupt:
                    print("\n⏹️  Interrumpido por usuario - terminando proceso...")
                    stop_thread.set()
                    process.terminate()
                    process.wait(timeout=5)
                    
                # Escribir pie
                log_file.write(f"\n{'='*60}\n")
                log_file.write(f"Fin: {datetime.now()}\n")
                log_file.write(f"Código salida: {process.returncode}\n")
                log_file.write(f"{'='*60}\n")
                
                return process.returncode
                
        except Exception as e:
            print(f"❌ Error crítico: {e}")
            import traceback
            traceback.print_exc()
            return 1

def print_usage():
    """Muestra ayuda de uso"""
    print("""
📋 LOGGER.PY - Capturador de Logs para Python
Versión 2.0 - Soporte mejorado para Windows

Uso:
  python logger.py run <script.py> [args...]    Ejecuta script capturando logs
  python logger.py help                         Muestra esta ayuda

Ejemplos:
  python logger.py run app.py
  python logger.py run app.py --port 8080 --debug
""")

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
        
    command = sys.argv[1].lower()
    
    if command == "run":
        if len(sys.argv) < 3:
            print("❌ Error: Se requiere script a ejecutar")
            print("   Uso: python logger.py run <script.py> [args...]")
            sys.exit(1)
            
        script_path = sys.argv[2]
        script_args = sys.argv[3:]
        
        # Verificar que el script existe
        if not Path(script_path).exists():
            print(f"❌ Error: Archivo '{script_path}' no encontrado")
            sys.exit(1)
            
        # Configurar comando
        full_command = [sys.executable, script_path] + script_args
        
        # Ejecutar con captura
        log_manager = LogManager(app_name="app")
        capture = ConsoleCapture(log_manager)
        return_code = capture.run_application(full_command, "run")
        
        sys.exit(return_code)
        
    elif command in ("help", "--help", "-h"):
        print_usage()
        
    else:
        print(f"❌ Error: Comando desconocido '{command}'")
        print_usage()
        sys.exit(1)

if __name__ == "__main__":
    main()