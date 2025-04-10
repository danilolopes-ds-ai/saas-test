"""
Gerenciador de plugins para extensão do sistema.
"""
import importlib
import inspect
import logging
import os
import pkgutil
from typing import Any, Dict, List, Optional, Set, Type

from app.core.exceptions import InvalidPluginError, PluginNotFoundError


logger = logging.getLogger(__name__)


class Plugin:
    """
    Classe base para todos os plugins do sistema.
    
    Define a interface comum que todos os plugins devem implementar.
    """
    
    @property
    def id(self) -> str:
        """ID único do plugin."""
        raise NotImplementedError("Todo plugin deve implementar id")
    
    @property
    def version(self) -> str:
        """Versão do plugin."""
        raise NotImplementedError("Todo plugin deve implementar version")
    
    @property
    def name(self) -> str:
        """Nome amigável do plugin."""
        raise NotImplementedError("Todo plugin deve implementar name")
    
    def initialize(self) -> None:
        """Inicializa o plugin."""
        pass


class NichoPlugin(Plugin):
    """
    Classe base para plugins de nicho de mercado.
    
    Permite estender o sistema para diferentes nichos de mercado
    (ex: Pilates, Psicologia, Nutrição).
    """
    
    @property
    def nicho_id(self) -> str:
        """ID do nicho."""
        raise NotImplementedError("Todo plugin de nicho deve implementar nicho_id")
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """
        Retorna templates de mensagem específicos do nicho.
        
        Returns:
            Lista de templates.
        """
        return []
    
    def get_fields(self) -> List[Dict[str, Any]]:
        """
        Retorna campos customizados para o nicho.
        
        Returns:
            Lista de campos customizados.
        """
        return []
    
    def get_workflows(self) -> List[Dict[str, Any]]:
        """
        Retorna fluxos de trabalho específicos do nicho.
        
        Returns:
            Lista de fluxos de trabalho.
        """
        return []


class PluginManager:
    """
    Gerenciador de plugins do sistema.
    
    Responsável por descobrir, registrar e gerenciar plugins que estendem
    a funcionalidade do sistema.
    """
    
    def __init__(self):
        """Inicializa o gerenciador de plugins."""
        self._plugins: Dict[str, Dict[str, Plugin]] = {}
        self._plugin_instances: Dict[str, Plugin] = {}
        self._plugin_types: Set[str] = {"nicho", "integration", "workflow", "theme"}
        
        logger.info("Gerenciador de plugins inicializado")
    
    def register_plugin(self, plugin_type: str, plugin: Plugin) -> None:
        """
        Registra um plugin verificando interface e versão.
        
        Args:
            plugin_type: Tipo do plugin (nicho, integration, etc).
            plugin: Instância do plugin.
            
        Raises:
            InvalidPluginError: Se o plugin não implementar a interface correta.
        """
        plugin_id = plugin.id
        
        # Validar tipo de plugin
        if plugin_type not in self._plugin_types:
            raise InvalidPluginError(f"Tipo de plugin desconhecido: {plugin_type}")
        
        # Validar contrato da interface
        if not self._validate_plugin_interface(plugin_type, plugin):
            raise InvalidPluginError(f"Plugin {plugin_id} não implementa interface {plugin_type}")
        
        # Registrar plugin
        if plugin_type not in self._plugins:
            self._plugins[plugin_type] = {}
            
        # Verificar se já existe plugin com mesmo ID
        if plugin_id in self._plugin_instances:
            existente = self._plugin_instances[plugin_id]
            logger.warning(f"Plugin {plugin_id} já registrado (versão {existente.version}), substituindo por versão {plugin.version}")
            
        self._plugins[plugin_type][plugin_id] = plugin
        self._plugin_instances[plugin_id] = plugin
        
        # Inicializar plugin
        try:
            plugin.initialize()
            logger.info(f"Plugin registrado: {plugin.name} ({plugin_id}) v{plugin.version}")
        except Exception as e:
            logger.error(f"Erro ao inicializar plugin {plugin_id}: {str(e)}")
            # Manter o plugin registrado mesmo com erro na inicialização
    
    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """
        Retorna plugin por ID.
        
        Args:
            plugin_id: ID do plugin.
            
        Returns:
            O plugin encontrado ou None.
        """
        return self._plugin_instances.get(plugin_id)
    
    def get_plugins_by_type(self, plugin_type: str) -> List[Plugin]:
        """
        Retorna todos os plugins de um tipo.
        
        Args:
            plugin_type: Tipo do plugin.
            
        Returns:
            Lista de plugins do tipo especificado.
        """
        return list(self._plugins.get(plugin_type, {}).values())
    
    def get_nicho_plugin(self, nicho_id: str) -> Optional[NichoPlugin]:
        """
        Retorna plugin de nicho pelo ID do nicho.
        
        Args:
            nicho_id: ID do nicho.
            
        Returns:
            O plugin do nicho ou None.
        """
        plugins = self.get_plugins_by_type("nicho")
        for plugin in plugins:
            if isinstance(plugin, NichoPlugin) and plugin.nicho_id == nicho_id:
                return plugin
        return None
    
    def discover_plugins(self, plugins_package: str = "app.plugins") -> None:
        """
        Descobre automaticamente e registra plugins disponíveis.
        
        Args:
            plugins_package: Pacote base para buscar plugins.
        """
        logger.info(f"Descobrindo plugins em {plugins_package}")
        
        try:
            # Importar o pacote base
            package = importlib.import_module(plugins_package)
            package_path = getattr(package, "__path__", None)
            
            if not package_path:
                logger.warning(f"Pacote {plugins_package} não tem subpacotes")
                return
            
            # Buscar subpacotes
            for _, name, is_pkg in pkgutil.iter_modules(package_path):
                if is_pkg:
                    self._discover_plugins_in_package(f"{plugins_package}.{name}")
        except Exception as e:
            logger.error(f"Erro ao descobrir plugins: {str(e)}")
    
    def _discover_plugins_in_package(self, package_name: str) -> None:
        """
        Descobre plugins em um pacote específico.
        
        Args:
            package_name: Nome do pacote para buscar.
        """
        try:
            # Determinar tipo de plugin pelo nome do pacote
            plugin_type = package_name.split(".")[-1]
            
            # Se não for um tipo válido, pular
            if plugin_type not in self._plugin_types:
                return
            
            # Importar o pacote
            package = importlib.import_module(package_name)
            
            # Buscar por módulos no pacote
            package_path = getattr(package, "__path__", None)
            if not package_path:
                return
            
            for _, name, _ in pkgutil.iter_modules(package_path):
                module_name = f"{package_name}.{name}"
                self._load_plugin_from_module(module_name, plugin_type)
        except Exception as e:
            logger.error(f"Erro ao descobrir plugins em {package_name}: {str(e)}")
    
    def _load_plugin_from_module(self, module_name: str, plugin_type: str) -> None:
        """
        Carrega plugins de um módulo.
        
        Args:
            module_name: Nome do módulo.
            plugin_type: Tipo de plugin esperado.
        """
        try:
            # Importar o módulo
            module = importlib.import_module(module_name)
            
            # Buscar classes que são plugins
            plugin_classes = self._find_plugin_classes(module, plugin_type)
            
            # Instanciar e registrar cada plugin
            for plugin_class in plugin_classes:
                try:
                    plugin_instance = plugin_class()
                    self.register_plugin(plugin_type, plugin_instance)
                except Exception as e:
                    logger.error(f"Erro ao instanciar plugin da classe {plugin_class.__name__}: {str(e)}")
        except Exception as e:
            logger.error(f"Erro ao carregar plugin do módulo {module_name}: {str(e)}")
    
    def _find_plugin_classes(self, module: Any, plugin_type: str) -> List[Type[Plugin]]:
        """
        Encontra classes de plugin em um módulo.
        
        Args:
            module: Módulo para buscar.
            plugin_type: Tipo de plugin esperado.
            
        Returns:
            Lista de classes de plugin.
        """
        result = []
        
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Pular classes importadas de outros módulos
            if obj.__module__ != module.__name__:
                continue
            
            # Verificar se é um plugin do tipo correto
            if plugin_type == "nicho" and issubclass(obj, NichoPlugin) and obj != NichoPlugin:
                result.append(obj)
            elif issubclass(obj, Plugin) and obj != Plugin and obj != NichoPlugin:
                # Para outros tipos, verificar pelo nome da classe
                if plugin_type.capitalize() in name:
                    result.append(obj)
        
        return result
    
    def _validate_plugin_interface(self, plugin_type: str, plugin: Any) -> bool:
        """
        Valida se o plugin implementa a interface correta.
        
        Args:
            plugin_type: Tipo do plugin.
            plugin: Instância do plugin.
            
        Returns:
            True se válido, False caso contrário.
        """
        # Verificar interface básica de Plugin
        if not isinstance(plugin, Plugin):
            return False
        
        # Verificar interfaces específicas
        if plugin_type == "nicho":
            return isinstance(plugin, NichoPlugin)
        
        # Por enquanto, outros tipos só precisam implementar a interface básica
        return True
