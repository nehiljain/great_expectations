anonymized_name_schema = {
   "$schema": "http://json-schema.org/schema#",
   "type": "string",
   "minLength": 32,
   "maxLength": 32,
}

anonymized_datasource_schema = {
   "$schema": "http://json-schema.org/schema#",
   "title": "anonymized-datasource",
   "definitions": {
      "anonymized_name": anonymized_name_schema
   },
   "oneOf": [
      {
         "type": "object",
         "properties": {
            "anonymized_name": {
               "$ref": "#/definitions/anonymized_name"
            },
            "parent_class": {
               "type": "string",
               "maxLength": 256
            },
            "anonymized_class": {
               "$ref": "#/definitions/anonymized_name"
            },
            "engine": {
               "type": "string",
               "maxLength": 256,
            }
         },
         "additionalProperties": False,
         "required": [
            "parent_class"
         ]
      }
   ]
}


anonymized_store_schema = {
   "$schema": "http://json-schema.org/schema#",
   "title": "anonymized-store",
   "definitions": {
      "anonymized_name": anonymized_name_schema
   },
   "oneOf": [
      {
         "type": "object",
         "properties": {
            "anonymized_name": {
               "$ref": "#/definitions/anonymized_name"
            },
            "parent_class": {
               "type": "string",
               "maxLength": 256
            },
            "anonymized_class": {
               "$ref": "#/definitions/anonymized_name"
            },
            "parent_backend": {
               "type": "string",
               "maxLength": 256
            },
            "anonymized_backend": {
               "$ref": "#/definitions/anonymized_name"
            }
         },
         "additionalProperties": False,
         "required": [
            "parent_class"
         ]
      }
   ]
}

init_payload_schema = {
   "$schema": "https://json-schema.org/schema#",
   "definitions": {
      "anonymized_datasource": anonymized_datasource_schema,
      "anonymized_store": anonymized_store_schema,
   },
   "type": "object",
   "properties": {
      "version": {
         "enum": ["1.0.0"]
      },
      "platform.system": {
         "type": "string",
         "maxLength": 256
      },
      "platform.release": {
         "type": "string",
         "maxLength": 256
      },
      "version_info": {
         "type": "string",
         "maxLength": 256
      },
      "anonymized_datasources": {
         "type": "array",
         "maxItems": 1000,
         "items": {
            "$ref": "#/definitions/anonymized_datasource"
         }
      },
      "anonymized_stores": {
         "type": "array",
         "maxItems": 1000,
         "items": {
            "$ref": "#/definitions/anonymized_store"
         }
      },
      "anonymized_validation_operators": {
         "type": "array",
         "maxItems": 1000,
         "items": {
            "type": "object"
         },
      },
   },
   "required": [
      "platform.system",
      "platform.release",
      "version_info",
      "anonymized_datasources",
   ],
   "additionalProperties": False
}

run_validation_operator_payload_schema = {
   "$schema": "http://json-schema.org/schema#",
   "type": "object",
   "properties": {
      "anonymized_operator_name": {
         "type": "string",
         "maxLength": 256,
      },
      "anonymized_datasource_name": {
         "type": "string",
         "maxLength": 256,
      },
      "anonymized_batch_kwargs": {
         "type": "array",
         "maxItems": 10,
         "items": {
            "type": "string",
            "maxLength": 256,
         }
      },
      "n_assets": {
         "type": "number"
      }
   },
   "required": [
      "anonymized_operator_name",
      # "anonymized_datasource_name",
      # "anonymized_batch_kwargs"
   ],
   "additionalProperties": False
}

usage_statistics_record_schema = {
   "$schema": "http://json-schema.org/schema#",
   "definitions": {
      "anonymized_name": anonymized_name_schema,
      "anonymized_datasource": anonymized_datasource_schema,
      "anonymized_store": anonymized_store_schema,
      "init_payload": init_payload_schema,
      "run_validation_operator_payload": run_validation_operator_payload_schema,
   },
   "type": "object",
   "properties": {
      "version": {
         "enum": ["1.0.0"]
      },
      "event_time": {
         "type": "string",
         "format": "date-time"
      },
      "data_context_id": {
         "type": "string",
         "format": "uuid"
      },
      "data_context_instance_id": {
         "type": "string",
         "format": "uuid"
      },
      "ge_version": {
         "type": "string",
         "maxLength": 32
      },
      "success": {
         "type": ["boolean", "null"]
      },
   },
   "oneOf": [
      {
         "type": "object",
         "properties": {
            "event": {
               "enum": ["data_context.__init__"],
            },
            "event_payload": {
               "$ref": "#/definitions/init_payload"
            }
         }
      },
      {
         "type": "object",
         "properties": {
            "event": {
               "enum": ["data_context.run_validation_operator"],
            },
            "event_payload": {
               "$ref": "#/definitions/run_validation_operator_payload"
            },
         }
      }
   ],
   "required": [
      "version",
      "event_time",
      "data_context_id",
      "data_context_instance_id",
      "ge_version",
      "event",
      "success",
      "event_payload"
   ]
}