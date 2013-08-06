from pyrox.http import HttpResponse


"""
Action enumerations.
"""
NEXT_FILTER = 0
CONSUME = 1
REJECT = 2


class FilterAction(object):
    """
    A filter action allows us to tell upstream controls what the filter has
    decided as the next course of action. Certain filter actions may include
    a resposne object for serialization out to the client in the case where
    the action enforces a rejection.

    Attributes:
        kind        An integer value representing the kind of action this
                    object is intended to communicate.
        response    A HttpResponse object to be rendered to the client when
                    this action is consumed.
    """
    def __init__(self, kind=NEXT_FILTER, response=None):
        self.kind = kind
        self.response = response

    def is_consuming(self):
        return self.kind == CONSUME

    def is_rejecting(self):
        return self.kind == REJECT


class HttpFilterChain(object):
    """
    The filter chain represents a filter pipeline. This pipeline currently
    serves bidirectional filtering (request and response). This chain will have
    the request head and response head events passed through it during the
    lifecycle of a client request. Each request is assigned a new copy of the
    chain, meaning that state may not be shared between requests during the
    lifetime of the filter chain or its filters.


    Attributes:
        chain       A list of HttpFilter objects organized to act as a pipeline
                    with element 0 being the first to recieve events.
    """
    def __init__(self):
        self.chain = list()

    def add_filter(self, http_filter):
        self.chain.append(http_filter)

    def on_request(self, request):
        last_action = pass_event()

        for http_filter in self.chain:
            try:
                action = http_filter.on_request(request)
            except Exception as ex:
                # TODO:Implement - Handle this error
                action = reject()
            if (action):
                last_action = action
                if action.is_consuming() or action.is_rejecting():
                    break

        return last_action

    def on_response(self, response):
        last_action = pass_event()

        for http_filter in self.chain:
            try:
                action = http_filter.on_response(response)
            except Exception as ex:
                # TODO:Implement - Handle this error
                action = reject()
            if (action):
                last_action = action
                if action.is_consuming() or action.is_rejecting():
                    break

        return last_action


class HttpFilter(object):

    def on_request(self, request_message):
        """
        on_request will accept an HttpRequest object and implement
        the logic that will define the FilterActions to be applied
        to the request
        """
        return pass_event()

    def on_response(self, response_message):
        """
        on_response will accept an HttpResponse object and implement
        the logic that will define the FilterActions to be applied
        to the request
        """
        return pass_event()

"""
Default return object. This should be configurable.
"""
_DEFAULT_REJECT_RESP = HttpResponse()
_DEFAULT_REJECT_RESP.version = b'1.1'
_DEFAULT_REJECT_RESP.status_code = 400
_DEFAULT_REJECT_RESP.header('Content-Length').values.append('0')

"""
Default filter action singletons.
"""
_DEFAULT_PASS_ACTION = FilterAction(NEXT_FILTER)
_DEFAULT_CONSUME_ACTION = FilterAction(CONSUME)


def consume():
    """
    Consumes the event and does not allow any further downstream filsters to
    see it. This effectively halts exectuion of the filter chain but leaves the
    request to pass through the proxy.
    """
    return _DEFAULT_CONSUME_ACTION


def reject(response=None):
    """
    Rejects the request that this event is related to. Rejection may happen
    during on_request and on_response. The associated response parameter
    becomes the response the client should expect to see. If a response
    parameter is not provided then the function will default to the configured
    default response.
    """
    return FilterAction(REJECT, response) if response\
        else FilterAction(REJECT, _DEFAULT_REJECT_RESP)


def pass_event():
    """
    Passes the current http event down the filter chain. This allows for
    downstream filters a chance to process the event.
    """
    return _DEFAULT_PASS_ACTION