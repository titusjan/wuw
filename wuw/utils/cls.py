""" Functions for type and class checks.
"""
import logging

logger = logging.getLogger(__name__)


def class_name(obj):
    """ Returns human-readable class name of the object ``obj``.
    """
    return obj.__class__.__name__


def check_is_sub_class(cls, class_info, allow_none=False):
    """ Raises TypeError if cls is not a subclass of class_info
    """
    if not (allow_none and cls is None) and not issubclass(cls, class_info):
        raise TypeError("Unexpected type {}, was expecting {}".format(type(cls), class_info))


def check_type(obj, class_info, allow_none=False):
    """ Raises TypeError if obj is not an instance of class_info
    """
    logger.debug(f"check_type: {obj}, class_info {class_info}")
    if not isinstance(obj, class_info) and not (allow_none and obj is None):
        raise TypeError("Unexpected type {}, was expecting {}".format(type(obj), class_info))



def check_is_callable(obj, allow_none=False):
    """ Checks that obj is callable.
        Raises TypeError if this is not the case. Otherwise does nothing.
    """
    if not (callable(obj) or (allow_none and obj is None)):
        raise TypeError("Object should be a callable: {}".format(obj))


def check_is_a_type(obj, allow_none=False):
    """ Raises type error if obj is not a type.

        :param: allow_none: whether None should pass the check. Default=False
    """
    check_type(obj, type, allow_none=allow_none)

