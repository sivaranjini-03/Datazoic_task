import json, logging, time, uuid

class JsonLogger:
    def __init__(self,name='paypal-agent'):
        self.log=logging.getLogger(name)
        if not self.log.handlers:
            h=logging.StreamHandler(); h.setFormatter(logging.Formatter('%(message)s')); self.log.addHandler(h); self.log.setLevel(logging.INFO)
    def event(self,event,**fields):
        self.log.info(json.dumps({'event':event,'trace_id':fields.pop('trace_id',str(uuid.uuid4())),'ts':time.time(),**fields},default=str))

logger=JsonLogger()
