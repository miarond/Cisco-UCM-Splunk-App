"""
XML payloads documented here:

https://developer.cisco.com/docs/sxml/#!perfmon-api
"""
perfmonAddCounter = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soap="http://schemas.cisco.com/ast/soap">
   <soapenv:Header/>
   <soapenv:Body>
      <soap:perfmonAddCounter>
         <soap:SessionHandle></soap:SessionHandle>
         <soap:ArrayOfCounter>
            <soap:Counter>
               <soap:Name></soap:Name>
            </soap:Counter>
         </soap:ArrayOfCounter>
      </soap:perfmonAddCounter>
   </soapenv:Body>
</soapenv:Envelope>
"""
perfmonCloseSession = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soap="http://schemas.cisco.com/ast/soap">
   <soapenv:Header/>
   <soapenv:Body>
      <soap:perfmonCloseSession>
         <soap:SessionHandle></soap:SessionHandle>
      </soap:perfmonCloseSession>
   </soapenv:Body>
</soapenv:Envelope>
"""
perfmonCollectCounterData = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soap="http://schemas.cisco.com/ast/soap">
   <soapenv:Header/>
   <soapenv:Body>
      <soap:perfmonCollectCounterData>
         <soap:Host></soap:Host>
         <soap:Object></soap:Object>
      </soap:perfmonCollectCounterData>
   </soapenv:Body>
</soapenv:Envelope>
"""
perfmonCollectSessionData = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soap="http://schemas.cisco.com/ast/soap">
   <soapenv:Header/>
   <soapenv:Body>
      <soap:perfmonCollectSessionData>
         <soap:SessionHandle></soap:SessionHandle>
      </soap:perfmonCollectSessionData>
   </soapenv:Body>
</soapenv:Envelope>
"""
perfmonListCounter = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soap="http://schemas.cisco.com/ast/soap">
   <soapenv:Header/>
   <soapenv:Body>
      <soap:perfmonListCounter>
         <soap:Host></soap:Host>
      </soap:perfmonListCounter>
   </soapenv:Body>
</soapenv:Envelope>
"""
perfmonOpenSession = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soap="http://schemas.cisco.com/ast/soap">
   <soapenv:Header/>
   <soapenv:Body>
      <soap:perfmonOpenSession/>
   </soapenv:Body>
</soapenv:Envelope>
"""