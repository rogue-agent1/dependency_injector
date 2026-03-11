#!/usr/bin/env python3
"""dependency_injector — IoC container with autowiring and scopes. Zero deps."""
import inspect

class Container:
    def __init__(self):
        self._registry = {}
        self._singletons = {}
        self._scoped = {}

    def register(self, interface, impl=None, scope='transient'):
        if impl is None: impl = interface
        self._registry[interface] = (impl, scope)

    def singleton(self, interface, impl=None):
        self.register(interface, impl, 'singleton')

    def resolve(self, interface):
        if interface not in self._registry:
            raise KeyError(f"Not registered: {interface}")
        impl, scope = self._registry[interface]
        if scope == 'singleton':
            if interface not in self._singletons:
                self._singletons[interface] = self._create(impl)
            return self._singletons[interface]
        return self._create(impl)

    def _create(self, impl):
        if callable(impl) and inspect.isclass(impl):
            sig = inspect.signature(impl.__init__)
            params = list(sig.parameters.values())[1:]  # skip self
            args = []
            for p in params:
                if p.annotation != inspect.Parameter.empty and p.annotation in self._registry:
                    args.append(self.resolve(p.annotation))
                elif p.default != inspect.Parameter.empty:
                    args.append(p.default)
                else:
                    raise ValueError(f"Cannot resolve param: {p.name}")
            return impl(*args)
        return impl

    def __getitem__(self, key): return self.resolve(key)

def main():
    # Example services
    class Logger:
        def log(self, msg): print(f"    LOG: {msg}")

    class Database:
        def __init__(self, logger: Logger):
            self.logger = logger
        def query(self, sql):
            self.logger.log(f"Query: {sql}")
            return [{"id": 1, "name": "Alice"}]

    class UserService:
        def __init__(self, db: Database, logger: Logger):
            self.db, self.logger = db, logger
        def get_user(self, uid):
            self.logger.log(f"Getting user {uid}")
            return self.db.query(f"SELECT * FROM users WHERE id={uid}")

    container = Container()
    container.singleton(Logger)
    container.register(Database)
    container.register(UserService)

    print("Dependency Injection Container:\n")
    svc = container.resolve(UserService)
    result = svc.get_user(1)
    print(f"  Result: {result}")
    # Verify singleton
    l1 = container.resolve(Logger)
    l2 = container.resolve(Logger)
    print(f"  Logger singleton: {l1 is l2}")

if __name__ == "__main__":
    main()
