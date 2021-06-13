from jsonschema import validate

# A sample schema, like what we'd get from json.load()
schema = {
	"type" : "object",
	"properties" : {
		"price" : {"type" : "number", "minimum": 0, "maximum": 30},
		"name" : {"type" : "string"},
	},
}

# If no exception is raised by validate(), the instance is valid.
validate(instance={"name" : "Eggs", "price" : 34.99}, schema=schema)	
validate(
	instance={"name" : "Eggs", "price" : "Invalid"}, schema=schema,
)                                   # doctest: +IGNORE_EXCEPTION_DETAIL
""" result =>
jsonschema.exceptions.ValidationError: 'Invalid' is not of type 'number'

Failed validating 'type' in schema['properties']['price']:
    {'type': 'number'}

On instance['price']:
    'Invalid'
"""
