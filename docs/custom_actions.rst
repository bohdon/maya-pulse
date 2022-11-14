Custom Actions
==============

Pulse comes with a default set of built-in actions, which are the building blocks that run modular rigging code.
Adding custom actions is easy and essential to custom rigging functionality.

Registering Action Packages
---------------------------

Actions are found by recursively searching a python package for :py:class:`~pulse.core.build_items.BuildAction`
subclasses. Beyond the default :py:mod:`pulse.builtin_actions`, you can add other action packages to search using the
:py:class:`BuildActionPackageRegistry`:

.. code-block:: python

    from pulse.core import BuildActionPackageRegistry
    import my_pulse_actions

    BuildActionPackageRegistry.get().add_package(my_pulse_actions)

In the above example, ``my_pulse_actions`` is a package with as many subpackages and submodules as you want.
An example structure might include sub-packages for organization, and one module per action:

.. code-block:: text

    my_pulse_actions/
      __init__.py
      first_group/
        __init__.py
        my_action_a.py
        my_action_b.py
      second_group/
        __init__.py
        my_action_c.py
        my_action_d.py

As long as all modules are at least imported in the package, they and all :py:class:`BuildAction` subclasses inside
them will be found. You can import all actions recursively to the root of the package with
:py:func:`~pulse.core.loader.import_all_submodules`. This allows any new actions to automatically be picked up without
having to individually import them:

.. code-block:: python

    # my_pulse_actions/__init__.py
    from pulse.core import import_all_submodules

    # equivalent to:
    #   import first_group.my_action_a
    #   import first_group.my_action_b
    #   import second_group.my_action_c
    #   import second_group.my_action_d
    import_all_submodules(__name__)


Implementing Actions
--------------------

Actions are as simple as executing a single function when it's their turn. Each action can expose as many attributes
as needed for the user to custom how individual action instances behave, such as what nodes to affect or which
settings to use for an operation.

Subclass :py:class:`~pulse.core.build_items.BuildAction`, set an ``id``, and implement the
:py:func:`~pulse.core.build_items.BuildAction.run` method:

.. code-block:: python

    from pulse.core import BuildAction, BuildActionError
    from pulse.core import BuildActionAttributeType as AttrType


    class MyAction(BuildAction):
        """
        An example action that logs some info.
        """

        id = 'MyStudio.MyAction'
        display_name = 'My Action'
        color = [.8, .4, .6]
        category = 'Custom'
        attr_definitions = [
            dict(name='myName', type=AttrType.STRING, value='Hello World'),
            dict(name='myNode', type=AttrType.NODE, description="A node attribute."),
            dict(name='myOption', type=AttrType.OPTION, value=1, options=['A', 'B', 'C']),
        ]

        def run(self):
            self.logger.info(f'My Name: {self.myName}')
            self.logger.info(f'My Node: {self.myNode}')
            self.logger.info(f'My Option: {self.myOption}')



Custom Action Editor Forms
--------------------------

TODO
