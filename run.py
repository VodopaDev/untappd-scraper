import logging
from thespian.actors import *
from logsetup import logcfg 

class Hello(Actor):
    def receiveMessage(self, message, sender):
        logging.info(message)
        self.send(sender, "cool")
        
if __name__ == "__main__":
    actorsys = ActorSystem(systemBase="multiprocQueueBase", logDefs=logcfg)
    for i in range(5):
        actor = actorsys.createActor(Hello)
        actorsys.tell(actor, "hey")