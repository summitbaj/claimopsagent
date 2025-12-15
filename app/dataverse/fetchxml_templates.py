# FetchXML templates for Dataverse queries

FETCHXML_CLAIM = '''
<fetch version="1.0" output-format="xml-platform" mapping="logical" distinct="true" page="1" count="1" no-lock="false">
    <entity name="smvs_claim">
        <attribute name="smvs_name"/>
        <attribute name="statecode"/>
        <attribute name="smvs_claimid"/>
        <attribute name="smvs_box26patientsaccountnumber"/>
        <link-entity alias="patient" name="contact" to="smvs_patientid" from="contactid" link-type="outer">
            <attribute name="fullname"/>
            <attribute name="birthdate"/>
        </link-entity>
        <attribute name="smvs_claimstatus"/>
        <attribute name="createdon"/>
        <attribute name="smvs_recieved_amount"/>
        <attribute name="smvs_claimed_amount"/>
        <attribute name="smvs_claimstatus835"/>
        <attribute name="smvs_claimnotes"/>
        <attribute name="smvs_remark"/>
        <attribute name="smvs_error_description"/>
        <link-entity alias="insurance" name="smvs_patient_insurance" to="smvs_patient_insurance" from="smvs_patient_insuranceid" link-type="outer">
            <attribute name="smvs_health_insurance_company"/>
            <attribute name="smvs_insurance_type"/>
        </link-entity>
        <attribute name="smvs_fulfilleddate"/>
        <attribute name="owningbusinessunit"/>
        <attribute name="modifiedon"/>
        <attribute name="modifiedby"/>
        <attribute name="smvs_claim_type"/>
        <order attribute="createdon" descending="true"/>
        <link-entity alias="payment_info" name="smvs_payment_information" to="smvs_payment_information_id" from="smvs_payment_informationid" link-type="outer">
            <attribute name="smvs_workers_comp_payer"/>
        </link-entity>
        <attribute name="smvs_expected_amount_claim"/>
        {filter}
    </entity>
</fetch>
'''

FETCHXML_HISTORICAL_CLAIMS = FETCHXML_CLAIM.replace('count="1"', 'count="50"')

FETCHXML_SERVICE_LINES = '''
<fetch version="1.0" output-format="xml-platform" mapping="logical" distinct="true" savedqueryid="411d3d4b-2125-ee11-9cbe-6045bd03848f" returntotalrecordcount="true" page="1" count="50" no-lock="false">
  <entity name="smvs_serviceline">
    <attribute name="smvs_name"/>
    <attribute name="statecode"/>
    <attribute name="smvs_servicelineid"/>
    <attribute name="smvs_ignoreforclaimsubmission"/>
    <attribute name="smvs_datesofservice"/>
    <attribute name="smvs_placeofservice"/>
    <attribute name="smvs_proceduresservicesorsupplies"/>
    <attribute name="smvs_modifiers"/>
    <attribute name="smvs_diagnosispointer"/>
    <attribute name="smvs_charges"/>
    <attribute name="smvs_daysorunits"/>
    <attribute name="smvs_dayorunitvalue"/>
    <attribute name="smvs_expected_amount_service_line"/>
    <attribute name="smvs_dateofserviceto"/>
    <attribute name="smvs_additional_modifiers"/>
    <attribute name="smvs_rendering_provider"/>
    <link-entity name="smvs_cpthcpcscode" from="smvs_cpthcpcscodeid" to="smvs_cpt_hcpcs_code" link-type="outer" alias="cpt" visible="false">
      <attribute name="smvs_description"/>
    </link-entity>
    <filter type="and">
        <condition attribute="smvs_claimid" operator="eq" value="{claim_id}" />
    </filter>
  </entity>
</fetch>
'''
