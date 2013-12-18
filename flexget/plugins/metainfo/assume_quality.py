from __future__ import unicode_literals, division, absolute_import
from flexget.plugin import register_plugin, priority, PluginError
from collections import namedtuple
import logging
import flexget.utils.qualities as qualities

log = logging.getLogger('assume_quality')


class AssumeQuality(object):
    """
    Applies quality components to entries that match specified quality requirements.

    Examples:
    assume_quality: 1080p webdl 10bit truehd

    assume_quality:
      hdtv: 720p
      720p hdtv: 10bit
      everything: 720p h264
    """

    schema = {
        'oneOf': [
            {'title':'simple config', 'type': 'string', 'format': 'quality'},
            {'title':'advanced config', 'type': 'object', 'properties': {
                           'target': {'type': 'string', 'format': 'quality'},
                           'quality': {'type': 'string', 'format': 'quality'}
                           }
            }
        ]
    }

    def precision(self, qualityreq):
        p = 0
        if qualityreq == 'everything': return -1000
        for component in qualityreq.components:
            if component.acceptable: p += 2
            if component.none_of: p -= 2
            if component.min: p += 1
            if component.max: p += 1
            #Still a long way from perfect, but probably good enough.
        return p

    def assume(self, entry, quality):
        newquality = qualities.Quality()
        log.debug('Current qualities: %s', entry.get('quality'))
        for component in entry.get('quality').components:
            qualitycomponent = getattr(quality, component.type)
            log.debug('\t%s: %s vs %s', component.type, component.name, qualitycomponent.name)
            if component.name != 'unknown':
                log.debug('\t%s: keeping %s', component.type, component.name)
                setattr(newquality, component.type, component)
            elif qualitycomponent.name != 'unknown':
                log.debug('\t%s: assuming %s', component.type, qualitycomponent.name)
                setattr(newquality, component.type, qualitycomponent)
                entry['assumed_quality'] = True
            elif component.name == 'unknown' and qualitycomponent.name == 'unknown':
                log.debug('\t%s: got nothing', component.type)
        entry['quality'] = newquality
        log.debug('Quality updated: %s', entry.get('quality'))

    def on_task_start(self, task, config):
        if isinstance(config, basestring): config = {'everything': config}
        assume = namedtuple('assume', ['target', 'quality'])
        self.assumptions = []
        for target, quality in config.items():
            log.verbose('New assumption: %s is %s' % (target, quality))
            #'everything' seems to be as good a default flag as any.
            target = target.lower()
            if target != 'everything':
                try: target = qualities.Requirements(target)
                except: raise PluginError('%s is not a valid quality. Forgetting assumption.' % target)
            try: quality = qualities.get(quality)
            except: raise PluginError('%s is not a valid quality. Forgetting assumption.' % quality)
            self.assumptions.append(assume(target, quality))
        self.assumptions.sort(key=lambda assumption: self.precision(assumption.target), reverse=True)
        for assumption in self.assumptions:
            log.debug('Target %s - Priority %s' % (assumption.target, self.precision(assumption.target)))

    @priority(127)  #run after metainfo_quality@128
    def on_task_metainfo(self, task, config):
        for entry in task.entries:
            log.verbose('%s' % entry.get('title'))
            for assumption in self.assumptions:
                log.debug('Trying %s - %s' % (assumption.target, assumption.quality))
                if assumption.target == 'everything' or assumption.target.allows(entry.get('quality')):
                    log.debug('Match: %s' % assumption.target)
                    self.assume(entry, assumption.quality)
            log.verbose('New quality: %s', entry.get('quality'))

register_plugin(AssumeQuality, 'assume_quality', api_ver=2)
