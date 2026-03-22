class Condition:
    def __init__(self, field, operator, value):
        self.field = field
        self.operator = operator
        self.value = value


class QueryDSL:
    def __init__(self, conditions, time_filter=None):
        self.conditions = conditions
        self.time_filter = time_filter   #  NEW
