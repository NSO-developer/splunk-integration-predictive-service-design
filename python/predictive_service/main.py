# -*- mode: python; python-indent: 4 -*-
import ncs
import _ncs

from ncs.application import Service
from .splunk_api import *


# ------------------------
# SERVICE CALLBACK EXAMPLE
# ------------------------
class ServiceCallbacks(Service):

    # The create() callback is invoked inside NCS FASTMAP and
    # must always exist.
    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        _ncs.dp.action_set_timeout(tctx.uinfo,6000)
        self.log.info('Service create(service=', service._path, ')')
        #action=forecast(service.max_length, self.log)
        #if not action:
        #   self.log.error("Expected memory consumption close to the critical limit. Aborting service execution.")
        #   raise Exception("Expected memory consumption close to the critical limit. Aborting service execution.")
        #else:
        self.log.info("Expected memory consumption not close to the critical limit. Proceed with service execution.")
        vars = ncs.template.Variables()
        vars.add('MaxLen', service.max_length)
        template = ncs.template.Template(service)
        template.apply('predictive_service-template', vars)

    # The pre_modification() and post_modification() callbacks are optional,
    # and are invoked outside FASTMAP. pre_modification() is invoked before
    # create, update, or delete of the service, as indicated by the enum
    # ncs_service_operation op parameter. Conversely
    # post_modification() is invoked after create, update, or delete
    # of the service. These functions can be useful e.g. for
    # allocations that should be stored and existing also when the
    # service instance is removed.

    @Service.pre_modification
    def cb_pre_modification(self, tctx, op, kp, root, proplist):
         self.log.info('Service premod(service=', kp, ')')
         _ncs.dp.action_set_timeout(tctx.uinfo,6000)
         if op == _ncs.dp.NCS_SERVICE_CREATE:  
            service = ncs.maagic.cd(root, kp)
            action=forecast(service.max_length, self.log)
            if not action:
               raise Exception("Expected memory consumption close to the critical limit. Aborting service execution.")

    # @Service.post_modification
    # def cb_post_modification(self, tctx, op, kp, root, proplist):
    #     self.log.info('Service postmod(service=', kp, ')')


# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class Main(ncs.application.Application):
    def setup(self):
        # The application class sets up logging for us. It is accessible
        # through 'self.log' and is a ncs.log.Log instance.
        self.log.info('Main RUNNING')

        # Service callbacks require a registration for a 'service point',
        # as specified in the corresponding data model.
        #
        self.register_service('predictive_service-servicepoint', ServiceCallbacks)

        # If we registered any callback(s) above, the Application class
        # took care of creating a daemon (related to the service/action point).

        # When this setup method is finished, all registrations are
        # considered done and the application is 'started'.

    def teardown(self):
        # When the application is finished (which would happen if NCS went
        # down, packages were reloaded or some error occurred) this teardown
        # method will be called.

        self.log.info('Main FINISHED')
