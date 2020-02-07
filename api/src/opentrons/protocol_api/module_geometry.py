""" opentrons.protocol_api.module_geometry: classes and functions for modules
as deck objects

This module provides things like :py:class:`ModuleGeometry` and
:py:func:`load_module` to create and manipulate module objects as geometric
objects on the deck (as opposed to calling commands on them, which is handled
by :py:mod:`.module_contexts`)
"""

import json
import logging
import re
from typing import Any, Dict, Optional

import jsonschema  # type: ignore

from opentrons.system.shared_data import load_shared_data
from opentrons.types import Location, Point
from opentrons.protocols.types import APIVersion
from .definitions import MAX_SUPPORTED_VERSION, DeckItem, V2_MODULE_DEF_VERSION
from .labware import Labware


log = logging.getLogger(__name__)


class NoSuchModuleError(Exception):
    def __init__(self, message: str, requested_module: str) -> None:
        self.message = message
        self.requested_module = requested_module
        super().__init__()

    def __str__(self) -> str:
        return self.message


class ModuleGeometry(DeckItem):
    """
    This class represents an active peripheral, such as an Opentrons Magnetic
    Module, Temperature Module or Thermocycler Module. It defines the physical
    geometry of the device (primarily the offset that modifies the position of
    the labware mounted on top of it).
    """

    @classmethod
    def resolve_module_model(cls, module_name: str) -> str:
        """ Turn any of the supported load names into module model names """
        alias_map = {
            'magdeck': 'magneticModuleV1',
            'magnetic module': 'magneticModuleV1',
            'magnetic module gen2': 'magneticModuleV2',
            'tempdeck': 'temperatureModuleV1',
            'temperature module': 'temperatureModuleV1',
            'temperature module gen2': 'temperatureModuleV2',
            'thermocycler': 'thermocyclerV1',
            'thermocycler module': 'thermocyclerV1'
        }
        lower_name = module_name.lower()
        resolved_name = alias_map.get(lower_name, None)
        if not resolved_name:
            raise ValueError(f'{module_name} is not a valid module load name.\n'
                             'Valid names (ignoring case): '
                             '"' + '", "'.join(alias_map.keys()) + '"')
        return resolved_name

    @property
    def disambiguate_calibration(self) -> bool:
        # If a module is the parent of a labware it affects calibration
        return True

    def __init__(self,
                 display_name: str,
                 model: str,
                 offset: Point,
                 overall_height: float,
                 height_over_labware: float,
                 parent: Location,
                 api_level: APIVersion) -> None:
        """
        Create a Module for tracking the position of a module.

        Note that modules do not currently have a concept of calibration apart
        from calibration of labware on top of the module. The practical result
        of this is that if the module parent :py:class:`.Location` is
        incorrect, then acorrect calibration of one labware on the deck would
        be incorrect on the module, and vice-versa. Currently, the way around
        this would be to correct the :py:class:`.Location` so that the
        calibrated labware is targeted accurately in both positions.

        :param display_name: A human-readable display name of only the module
                             (for instance, "Thermocycler Module" - not
                             including parents or location)
        :param model: The model of module this represents
        :param offset: The offset from the slot origin at which labware loaded
                       on this module should be placed
        :param overall_height: The height of the module without labware
        :param height_over_labware: The height of this module over the top of
                                    the labware
        :param parent: A location representing location of the front left of
                       the outside of the module (usually the front-left corner
                       of a slot on the deck).
        :type parent: :py:class:`.Location`
        :param APIVersion api_level: the API version to set for the loaded
                                     :py:class:`ModuleGeometry` instance. The
                                     :py:class:`ModuleGeometry` will
                                     conform to this level.
        """
        self._api_version = api_level
        self._parent = parent
        self._display_name = "{} on {}".format(
            display_name, str(parent.labware))
        self._load_name = model
        self._offset = offset
        self._height = overall_height + self._parent.point.z
        self._over_labware = height_over_labware
        self._labware: Optional[Labware] = None
        self._location = Location(
            point=self._offset + self._parent.point,
            labware=self)

    @property
    def api_version(self) -> APIVersion:
        return self._api_version

    def add_labware(self, labware: Labware) -> Labware:
        assert not self._labware,\
            '{} is already on this module'.format(self._labware)
        self._labware = labware
        return self._labware

    def reset_labware(self):
        self._labware = None

    @property
    def load_name(self):
        return self._load_name

    @property
    def parent(self):
        return self._parent.labware

    @property
    def labware(self) -> Optional[Labware]:
        return self._labware

    @property
    def location(self) -> Location:
        """
        :return: a :py:class:`.Location` representing the top of the module
        """
        return self._location

    @property
    def labware_offset(self) -> Point:
        """
        :return: a :py:class:`.Point` representing the transformation
        between the critical point of the module and the critical
        point of its contained labware
        """
        return self._offset

    @property
    def highest_z(self) -> float:
        if self.labware:
            return self.labware.highest_z + self._over_labware
        else:
            return self._height

    def __repr__(self):
        return self._display_name


class ThermocyclerGeometry(ModuleGeometry):
    def __init__(self,
                 display_name: str,
                 model: str,
                 offset: Point,
                 overall_height: float,
                 height_over_labware: float,
                 lid_height: float,
                 parent: Location,
                 api_level: APIVersion) -> None:
        """
        Create a Module for tracking the position of a module.

        Note that modules do not currently have a concept of calibration apart
        from calibration of labware on top of the module. The practical result
        of this is that if the module parent :py:class:`.Location` is
        incorrect, then acorrect calibration of one labware on the deck would
        be incorrect on the module, and vice-versa. Currently, the way around
        this would be to correct the :py:class:`.Location` so that the
        calibrated labware is targeted accurately in both positions.

        :param display_name: A human-readable display name of only the module
                             (for instance, "Thermocycler Module" - not
                             including parents or location)
        :param model: The model of module this represents
        :param offset: The offset from the slot origin at which labware loaded
                       on this module should be placed
        :param overall_height: The height of the module without labware
        :param height_over_labware: The height of this module over the top of
                                    the labware
        :param parent: A location representing location of the front left of
                       the outside of the module (usually the front-left corner
                       of a slot on the deck).
        :type parent: :py:class:`.Location`
        :param APIVersion api_level: the API version to set for the loaded
                                     :py:class:`ModuleGeometry` instance. The
                                     :py:class:`ModuleGeometry` will
                                     conform to this level.
        """
        super().__init__(
            display_name, model, offset, overall_height,
            height_over_labware, parent, api_level)
        self._lid_height = lid_height
        self._lid_status = 'open'   # Needs to reflect true status
        # TODO: BC 2019-07-25 add affordance for "semi" configuration offset
        # to be from a flag in context, according to drawings, the only
        # difference is -23.28mm in the x-axis

    @property
    def highest_z(self) -> float:
        # TODO: BC 2019-08-27 this highest_z value represents the distance
        # from the top of the open TC chassis to the base. Once we have a
        # more robust collision detection system in place, the collision
        # model for the TC should change based on it's lid_status
        # (open or closed). A prerequisite for that check will be
        # path-specific highest z calculations, as opposed to the current
        # global check on instrument.move_to. For example: a move from slot 1
        # to slot 3 should only check the highest z of all deck items between
        # the source and destination in the x,y plane.
        return super().highest_z

    @property
    def lid_status(self) -> str:
        return self._lid_status

    @lid_status.setter
    def lid_status(self, status) -> None:
        self._lid_status = status

    # NOTE: this func is unused until "semi" configuration
    def labware_accessor(self, labware: Labware) -> Labware:
        # Block first three columns from being accessed
        definition = labware._definition
        definition['ordering'] = definition['ordering'][3::]
        return Labware(
            definition, super().location, api_level=self._api_version)

    def add_labware(self, labware: Labware) -> Labware:
        assert not self._labware,\
            '{} is already on this module'.format(self._labware)
        assert self.lid_status != 'closed', \
            'Cannot place labware in closed module'
        self._labware = labware
        return self._labware


def _load_from_v1(definition: Dict[str, Any],
                  parent: Location,
                  api_level: APIVersion) -> ModuleGeometry:
    """ Load a module geometry from a v1 definition.

    The definition should be schema checked before being passed to this
    function; all definitions passed here are assumed to be valid.
    """
    mod_name = definition['loadName']
    model_name = {'thermocycler': 'thermocyclerModuleV1',
                  'magdeck': 'magneticModuleV1',
                  'tempdeck': 'temperatureModuleV1'}[mod_name]
    offset = Point(definition["labwareOffset"]["x"],
                   definition["labwareOffset"]["y"],
                   definition["labwareOffset"]["z"])
    overall_height = definition["dimensions"]["bareOverallHeight"]\

    height_over_labware = definition["dimensions"]["overLabwareHeight"]

    if mod_name == 'thermocycler':
        lid_height = definition['dimensions']['lidHeight']
        mod: ModuleGeometry = \
            ThermocyclerGeometry(definition["displayName"],
                                 model_name,
                                 offset,
                                 overall_height,
                                 height_over_labware,
                                 lid_height,
                                 parent,
                                 api_level)
    else:
        mod = ModuleGeometry(definition['displayName'],
                             model_name,
                             offset,
                             overall_height,
                             height_over_labware,
                             parent, api_level)
    return mod


def _load_from_v2(definition: Dict[str, Any],
                  parent: Location,
                  api_level: APIVersion) -> ModuleGeometry:
    """ Load a module geometry from a v2 definition.

    The definition should be schema checked before being passed to this
     function; all definitions passed here are assumed to be valid.
    """
    pass


def load_module_from_definition(
        definition: Dict[str, Any],
        parent: Location,
        api_level: APIVersion = None) -> ModuleGeometry:
    """
    Return a :py:class:`ModuleGeometry` object from a specified definition
    matching the v1 module definition schema

    :param definition: A dict representing the full module definition adhering
                       to the v1 module schema
    :param parent: A :py:class:`.Location` representing the location where
                   the front and left most point of the outside of the module
                   is (often the front-left corner of a slot on the deck).
    :param APIVersion api_level: the API version to set for the loaded
                                 :py:class:`ModuleGeometry` instance. The
                                 :py:class:`ModuleGeometry` will
                                 conform to this level. If not specified,
                                 defaults to :py:attr:`.MAX_SUPPORTED_VERSION`.
    """
    api_level = api_level or MAX_SUPPORTED_VERSION
    schema = definition.get("$otSharedSchema")
    if not schema:
        # v1 definitions don't have schema versions
        return _load_from_v1(definition, parent, api_level)
    if schema == 'module/schemas/2':
        schema_doc = json.loads(load_shared_data("module/schemas/2.json"))
        try:
            jsonschema.validate(definition, schema_doc)
        except jsonschema.ValidationError:
            log.exception("Failed to validate module def schema")
            raise RuntimeError('The specified module definition is not valid.')
        return _load_from_v2(definition, parent, api_level)
    elif isinstance(schema, str):
        maybe_schema = re.match('^module/schemas/([0-9]+)$', schema)
        if maybe_schema:
            raise RuntimeError(
                f"Module definitions of schema version {maybe_schema.group(1)}"
                " are not supported in this robot software release.")
    log.error(f"Bad module definition (schema specifier {schema})")
    raise RuntimeError(
        f'The specified module definition is not valid.')


def _load_module_definition(api_level: APIVersion,
                            module_model) -> Dict[str, Any]:
    """
    Load the appropriate module definition for this api version
    """
    if api_level < V2_MODULE_DEF_VERSION:
        v1names = {'magneticModuleV1': 'magdeck',
                   'temperatureModuleV1': 'tempdeck',
                   'thermocyclerModuleV1': 'thermocycler'}
        try:
            name = v1names[module_model]
        except KeyError:
            raise NoSuchModuleError(
                f'API version {api_level} does not support the module '
                f'{module_model} Please use at least version'
                f'{V2_MODULE_DEF_VERSION} to use this module.', module_model)
        return json.loads(load_shared_data('module/definitions/1.json')[name])
    else:
        try:
            defn = json.loads(
                load_shared_data(f'module/definitions/2/{module_model}.json'))
        except OSError:
            raise NoSuchModuleError(
                f'Could not find the module {module_model}.', module_model)
        return defn

def load_module(
        name: str,
        parent: Location,
        api_level: APIVersion = None) -> ModuleGeometry:
    """
    Return a :py:class:`ModuleGeometry` object from a definition looked up
    by name.

    :param name: The module model to use. This should be one of the strings
                 returned by :py:func:`ModuleGeometry.resolve_module_model`
    :param parent: A :py:class:`.Location` representing the location where
                   the front and left most point of the outside of the module
                   is (often the front-left corner of a slot on the deck).
    :param APIVersion api_level: the API version to set for the loaded
                                 :py:class:`ModuleGeometry` instance. The
                                 :py:class:`ModuleGeometry` will
                                 conform to this level. If not specified,
                                 defaults to :py:attr:`.MAX_SUPPORTED_VERSION`.
    """
    api_level = api_level or MAX_SUPPORTED_VERSION
    defn = _load_module_definition(api_level, name)
    return load_module_from_definition(defn[name], parent, api_level)
