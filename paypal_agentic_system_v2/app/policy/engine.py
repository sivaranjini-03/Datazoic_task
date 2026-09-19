from app.exceptions import PolicyError

class PolicyEngine:
    def check(self, tool, confirmed=False):
        if tool.get('requires_confirmation') and not confirmed:
            return {'allowed':False,'requires_confirmation':True,'reason':f"'{tool['name']}' is classified as {tool.get('risk')} and requires user confirmation."}
        return {'allowed':True,'requires_confirmation':False}
