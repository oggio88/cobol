package {packageName};


@NSRModule(code = "I{serviceName}Connector", description = "{serviceName}Connector", version = "1.0")
public interface I{serviceName}Connector extends IGenericNSRModule
{{
    public {serviceName}ServiceResponse call{serviceName}(DaoExecutionDescriptor daoExecutionDescriptor,
            {serviceName}ServiceRequest request, {serviceName}ServiceResponse response) throws Exception;
}}