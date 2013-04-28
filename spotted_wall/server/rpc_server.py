"""
Stuff for the RPC server methods
"""
import threading
from smartrpyc.server import Server


class MethodsObject(object):
    """
    An object returning its own methods via the lookup()
    method. SmartRPyC MethodsRegister-compatible.
    """

    def register(self, *a, **kw):
        raise NotImplementedError

    def store(self, *a, **kw):
        raise NotImplementedError

    def lookup(self, method):
        return getattr(self, method)


class SpottedRpcMethods(MethodsObject):
    """
    Methods for the RPC.
    This is an object as we need to call methods on the underlying app.
    """
    def __init__(self, app):
        self.app = app

    @property
    def screen(self):
        return self.app.screen

    def add_message(self, request, *args, **kwargs):
        return self.screen.add_message(*args, **kwargs)

    def list_messages(self, request):
        return list(self.screen.list_messages())

    def delete_message(self, request, message_id):
        return self.screen.delete_message(message_id)

    def hide_message(self, request, message_id):
        return self.screen.hide_message(message_id)

    def update_message(self, request, message_id, values):
        return self.screen.update_message(message_id, values)

    def get_message(self, request, message_id):
        return self.screen.get_message(message_id)

    def server_info(self, request):
        return {
            'version': __import__('spotted_wall').__version__,
        }


class RPCServerThread(threading.Thread):

    daemon = True
    parent = None
    addresses = None
    
    def __init__(self, parent, addresses):
        self.parent = parent
        self.addresses = addresses
        super(RPCServerThread, self).__init__()
        self.rpc_server = Server(
            methods=SpottedRpcMethods(self.parent))

    def run(self):
        for address in self.addresses:
            self.rpc_server.bind(address)
        self.rpc_server.run()
