import mailbox

class Store(mailbox.mbox):
    pass

class Message(mailbox.mboxMessage):
    def __init__(self,
                 **kwargs):
        for f,v in kwargs.items():
            if f=='body':
                self.set_payload(v)
            else:
                self[f] = v
