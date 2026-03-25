class NotImplementedMeta(type):
    """
    A metaclass that replaces all parent class methods and properties that aren't overridden in the subclass
    with NotImplementedError.
    """

    def __new__(mcs, name, bases, namespace):
        # Get all attributes from base classes
        for base in bases:
            for attr_name in dir(base):
                if attr_name.startswith("_"):
                    continue

                # Skip if already defined in subclass
                if attr_name in namespace:
                    continue

                base_attr = getattr(base, attr_name)

                # Handle properties
                if isinstance(base_attr, property):
                    # Create a property that raises NotImplementedError
                    def make_not_implemented_property(prop_name):
                        def getter(self):
                            raise NotImplementedError(f"Property '{prop_name}' not implemented")

                        def setter(self, value):
                            raise NotImplementedError(f"Property '{prop_name}' not implemented")

                        def deleter(self):
                            raise NotImplementedError(f"Property '{prop_name}' not implemented")

                        return property(getter, setter, deleter)

                    namespace[attr_name] = make_not_implemented_property(attr_name)

                # Handle regular methods
                elif callable(base_attr):

                    def make_not_implemented(method_name):
                        def not_impl(self, *args, **kwargs):
                            raise NotImplementedError(f"Method '{method_name}' not implemented")

                        return not_impl

                    namespace[attr_name] = make_not_implemented(attr_name)

        return super().__new__(mcs, name, bases, namespace)
