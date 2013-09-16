from django.contrib.gis.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import RegexValidator
from django.utils.six import with_metaclass

from south.modelsinspector import add_introspection_rules

import hashlib
import json


URL_NAME_PATTERN = r'[a-z]+[a-z0-9\-]*'


class JSONField(with_metaclass(models.SubfieldBase, models.TextField)):
    def to_python(self, value):
        if isinstance(value, basestring):
            return json.loads(value or "{}")
        else:
            return value

    def get_prep_value(self, value):
        return json.dumps(value or {})

    def get_prep_lookup(self, lookup_type, value):
        raise TypeError("JSONField doesn't support lookups")

add_introspection_rules([], ["^treemap\.instance\.JSONField"])


class Instance(models.Model):
    """
    Each "Tree Map" is a single instance
    """
    name = models.CharField(max_length=255, unique=True)

    url_name = models.CharField(max_length=255, unique=True,
                                validators=[RegexValidator(
                                    r'^%s$' % URL_NAME_PATTERN,
                                    'Must start with a lowercase letter and '
                                    'may only contain lowercase letters, '
                                    'numbers, or dashes ("-")',
                                    'Invalid URL name')])

    """
    Basemap type     Basemap data
    ------------     -----------------
    Google           Google_API_Key
    Bing             Bing_API_Key
    TMS              TMS URL with {x},{y},{z}
    """
    basemap_type = models.CharField(max_length=255,
                                    choices=(("google", "Google"),
                                             ("bing", "Bing"),
                                             ("tms", "Tile Map Service")),
                                    default="google")
    basemap_data = models.CharField(max_length=255, null=True, blank=True)

    """
    The current database revision for the instance

    This revision is used to determine if tiles should be cached.
    In particular, the revision has *no* effect on the actual
    data.

    Generally we make tile requests like:
    http://tileserver/tile/{layer}/{rev}/{Z}/{Y}/{X}

    There is a database trigger that updates the
    revision whenever an edit to a geometry field is made
    so you don't have to worry about it.

    You should *not* edit this field.
    """
    geo_rev = models.IntegerField(default=1)

    eco_benefits_conversion = models.ForeignKey(
        'BenefitCurrencyConversion', null=True, blank=True)

    """ Center of the map when loading the instance """
    bounds = models.MultiPolygonField(srid=3857)

    default_role = models.ForeignKey('Role', related_name='default_role')

    users = models.ManyToManyField('User', through='InstanceUser',
                                   null=True, blank=True)

    boundaries = models.ManyToManyField('Boundary', null=True, blank=True)

    """
    Config contains a bunch of config variables for a given instance
    these can be accessed via per-config properties such as
    `advanced_search_fields`
    """
    config = JSONField(blank=True)

    is_public = models.BooleanField(default=False)

    objects = models.GeoManager()

    def __unicode__(self):
        return self.name

    def _make_config_property(prop, default=None):
        def get_config(self):
            return self.config[prop] or default

        def set_config(self, value):
            self.config[prop] = value

        return property(get_config, set_config)

    advanced_search_filters = _make_config_property(
        'advanced_search_fields')

    @property
    def center(self):
        return self.bounds.centroid

    @property
    def geo_rev_hash(self):
        return hashlib.md5(str(self.geo_rev)).hexdigest()

    @property
    def center_lat_lng(self):
        return self.center.transform(4326, clone=True)

    @property
    def advanced_search_fields(self):
        fields = (self.config['advanced_search_fields']
                  if 'advanced_search_fields' in self.config else [])
        return [{'identifier': field['identifier'],
                 'search_type': field.get('search_type', 'IS'),
                 'default': field.get('default'),
                 'label': field.get('label')}
                for field in fields]

    def is_accessible_by(self, user):
        try:
            if self.is_public:
                return True
            # If a user is not logged in, trying to check
            # user=user raises a type error so I am checking
            # pk instead
            self.instanceuser_set.get(user__pk=user.pk)
            return True
        except ObjectDoesNotExist:
            return False

    def scope_model(self, model):
        qs = model.objects.filter(instance=self)
        return qs

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Instance, self).save(*args, **kwargs)
