from pyrox.util.config import (load_config, ConfigurationPart,
                               ConfigurationError)


_DEFAULTS = {
    'core': {
        'processes': 1,
        'bind_host': 'localhost:8080'
    },
    'routing': {
        'upstream_hosts': 'localhost:80'
    },
    'pipeline': {
        'use_singletons': False
    },
    'templates': {
        'pyrox_error_sc': 502,
        'rejection_sc': 400
    },
    'logging': {
        'console': True,
        'logfile': None,
        'verbosity': 'WARNING'
    }
}


def _split_and_strip(values_str, split_on):
    if split_on in values_str:
        return (value.strip() for value in values_str.split(split_on))
    else:
        return (values_str,)


def _host_tuple(host_str):
    parts = host_str.split(':')

    if len(parts) == 1:
        return (parts[0], 80)
    elif len(parts) == 2:
        return (parts[0], int(parts[1]))
    else:
        raise ConfigurationError('Malformed host: {}'.format(host_str))


def load_pyrox_config(location='/etc/pyrox/pyrox.conf'):
    return load_config('pyrox.server.config', location, _DEFAULTS)


class CoreConfiguration(ConfigurationPart):
    """
    Class mapping for the Pyrox configuration section 'core'
    """
    @property
    def processes(self):
        """
        Returns the number of processes Pyrox should spin up to handle
        messages. If unset, this defaults to 1.

        Example
        --------
        processes = 0
        """
        return self.getint('processes')

    @property
    def plugin_paths(self):
        """
        Returns a list of directories to plug into when attempting to resolve
        the names of pipeline filters. This option may be a single directory or
        a comma delimited list of directories.

        Example
        -------
        plugin_paths = /usr/share/project/python
        plugin_paths = /usr/share/project/python,/usr/share/other/python
        """
        paths = self.get('plugin_paths')
        if paths:
            return [path for path in _split_and_strip(paths, ',')]
        else:
            return list()

    @property
    def bind_host(self):
        """
        Returns the host and port the proxy is expected to bind to when
        accepting connections. This option defaults to localhost:8080 if left
        unset.

        Example
        --------
        bind_host = localhost:8080
        """
        return self.get('bind_host')


class LoggingConfiguration(ConfigurationPart):
    """
    Class mapping for the Pyrox configuration section 'logging'
    """
    @property
    def console(self):
        """
        Returns a boolean representing whether or not Pyrox should write to
        stdout for logging purposes. This value may be either True of False. If
        unset this value defaults to False.
        """
        return self.get('console')

    @property
    def logfile(self):
        """
        Returns the log file the system should write logs to. When set, Pyrox
        will enable writing to the specified file for logging purposes If unset
        this value defaults to None.
        """
        return self.get('logfile')

    @property
    def verbosity(self):
        """
        Returns the type of log messages that should be logged. This value may
        be one of the following: DEBUG, INFO, WARNING, ERROR or CRITICAL. If
        unset this value defaults to WARNING.
        """
        return self.get('verbosity')


class PipelineConfiguration(ConfigurationPart):
    """
    Class mapping for the Pyrox configuration section 'pipeline'

    Configuring a pipeline requires the admin to first configure aliases to
    each filter referenced. This is done by adding a named configuration
    option to this section that does not match "upstream" or "downstream."
    Filter aliases must point to a class or function that returns a filter
    instance with the expected entry points.

    After the filter aliases are specified, they may be then organized in
    comma delimited lists and assigned to either the "upstream" option for
    filters that should receive upstream events or the "downstream" option
    for filters that should receive downstream events.

    In the context of Pyrox, upstream events originate from the requesting
    client also known as the request. Downstream events originate from the
    origin service (the upstream request target) and is also known as the
    response.

    Example Pipeline Configuration
    ---------------------
    filter_1 = myfilters.upstream.Filter1
    filter_2 = myfilters.upstream.Filter2
    filter_3 = myfilters.downstream.Filter3

    upstream = filter_1, filter_2
    downstream = filter_3
    """
    @property
    def use_singletons(self):
        """
        Returns a boolean value representing whether or not Pyrox should
        reuse filter instances for up and downstream aliases. This means,
        effectively, that a filter specified in both pipelines will
        maintain its state for the request and response lifecycle. If left
        unset this option defaults to false.
        """
        return self.getboolean('use_singletons')

    @property
    def upstream(self):
        """
        Returns the list of filters configured to handle upstream events.
        This configuration option must be a comma delimited list of filter
        aliases. If left unset this option defaults to an empty list.
        """
        return self._pipeline_for('upstream')

    @property
    def downstream(self):
        """
        Returns the list of filters configured to handle downstream events.
        This configuration option must be a comma delimited list of filter
        aliases. If left unset this option defaults to an empty tuple.
        """
        return self._pipeline_for('downstream')

    def _pipeline_for(self, stream):
        pipeline = list()
        filters = self._filter_dict()
        pipeline_str = self.get(stream)
        if pipeline_str:
            for pl_filter in _split_and_strip(pipeline_str, ','):
                if pl_filter in filters:
                    pipeline.append(filters[pl_filter])
        return pipeline

    def _filter_dict(self):
        filters = dict()
        for pfalias in self.options():
            if pfalias == 'downstream' or pfalias == 'upstream':
                continue
            filters[pfalias] = self.get(pfalias)
        return filters


class TemplatesConfiguration(ConfigurationPart):
    """
    Class mapping for the Pyrox configuration section 'templates'
    """
    @property
    def pyrox_error_sc(self):
        """
        Returns the status code to be set for any error that happens within
        Pyrox that would prevent normal service of client requests. If left
        unset this option defaults to 502.
        """
        return self.getint('pyrox_error_sc')

    @property
    def rejection_sc(self):
        """
        Returns the default status code to be set for client request
        rejection made with no provided response object to serialize. If
        left unset this option defaults to 400.
        """
        return self.getint('rejection_sc')


class RoutingConfiguration(ConfigurationPart):
    """
    Class mapping for the Pyrox configuration section 'routing'
    """
    @property
    def upstream_hosts(self):
        """
        Returns a list of downstream hosts to proxy requests to. This may be
        set to either a single host and port or a comma delimited list of hosts
        and their associated ports. This option defaults to localhost:80 if
        left unset.

        Examples
        --------
        upstream_hosts = host:port
        upstream_hosts = host:port,host:port,host:port
        upstream_hosts = host:port, host:port, host:port
        """
        hosts = self.get('upstream_hosts')
        return [_host_tuple(host) for host in _split_and_strip(hosts, ',')]