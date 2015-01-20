package {packageName};

import it.bpm.nsr.business.impl.pef.facility.GenericConnectorImpl;
import it.bpm.nsr.core.dao.DaoExecutionDescriptor;
import it.bpm.nsr.core.exceptions.GenericException;
import it.bpm.nsr.core.services.GenericServiceResponse;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

public class {serviceName}ConnectorImpl extends GenericConnectorImpl implements I{serviceName}Connector
{{

    @SuppressWarnings("unchecked")
    @Override
    public {serviceName}ServiceResponse call{serviceName}(DaoExecutionDescriptor daoExecutionDescriptor,
            {serviceName}ServiceRequest request, {serviceName}ServiceResponse response) throws Exception
    {{
        List<BeanName> lista = new ArrayList<BeanName>();
        HashMap<String, Object> results = daoExecutionDescriptor.getHashQueryResults();

        if(checkEsito(daoExecutionDescriptor, response, results)==GenericServiceResponse.ESITO_OK){{
            lista = (List<BeanName>) results.get("COBOL-NAME");
        }}
        return null;
    }}
}}
