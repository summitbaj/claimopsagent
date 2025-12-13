# FetchXML templates for Dataverse queries

FETCHXML_CLAIM = '''
<fetch version="1.0" output-format="xml-platform" mapping="logical" distinct="true" page="1" count="1" no-lock="false">
    <entity name="smvs_claim">
        <attribute name="smvs_name"/>
        <attribute name="statecode"/>
        <attribute name="smvs_claimid"/>
        <attribute name="smvs_box26patientsaccountnumber"/>
        <link-entity alias="a_577b8cb208d6413f86077e177b6d8d77" name="contact" to="smvs_patientid" from="contactid" link-type="outer" visible="false">
            <attribute name="fullname"/>
            <attribute name="birthdate"/>
        </link-entity>
        <attribute name="smvs_claimstatus"/>
        <attribute name="createdon"/>
        <attribute name="smvs_recieved_amount"/>
        <attribute name="smvs_claimed_amount"/>
        <attribute name="smvs_claimstatus835"/>
        <attribute name="smvs_claimnotes"/>
        <link-entity alias="a_b42c88d155f8435fabc8fa28a45eb472" name="smvs_patient_insurance" to="smvs_patient_insurance" from="smvs_patient_insuranceid" link-type="outer" visible="false">
            <attribute name="smvs_health_insurance_company"/>
            <attribute name="smvs_insurance_type"/>
        </link-entity>
        <attribute name="smvs_fulfilleddate"/>
        <attribute name="owningbusinessunit"/>
        <attribute name="modifiedon"/>
        <attribute name="modifiedby"/>
        <attribute name="smvs_claim_type"/>
        <order attribute="createdon" descending="true"/>
        <link-entity alias="a_d512c97d2ef84b49a1e3588e8ee94a94" name="smvs_payment_information" to="smvs_payment_information_id" from="smvs_payment_informationid" link-type="outer" visible="false">
            <attribute name="smvs_workers_comp_payer"/>
        </link-entity>
        <attribute name="smvs_expected_amount_claim"/>
        {filter}
    </entity>
</fetch>
'''

FETCHXML_HISTORICAL_CLAIMS = FETCHXML_CLAIM.replace('count="1"', 'count="50"')

FETCHXML_SERVICE_LINES = '''
<fetch version="1.0" output-format="xml-platform" mapping="logical" distinct="false" page="1" count="50" no-lock="false">
    <entity name="smvs_serviceline">
        <attribute name="smvs_servicelineid"/>
        <attribute name="smvs_name"/>
        <attribute name="smvs_proceduresservicesorsupplies"/>
        <attribute name="smvs_modifiers"/>
        <attribute name="smvs_charges"/>
        <attribute name="smvs_additional_modifiers"/>
        <attribute name="smvs_diagnosispointer"/>
        <attribute name="smvs_placeofservice"/>
        <attribute name="smvs_dayorunitvalue"/>
        <attribute name="smvs_datesofservice"/>
        <attribute name="smvs_dateofserviceto"/>
        <filter type="and">
            <condition attribute="_smvs_claimid_value" operator="eq" value="{claim_id}" />
        </filter>
    </entity>
</fetch>
'''
