import json
import random
import string
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool

@tool
def test_apigee_proxy_bundle(bundle_path: str, api_spec_path: Optional[str] = None, environment: str = "dev") -> str:
    """
    Simulates the comprehensive testing of an Apigee proxy bundle.
    This tool performs functional, performance, and security checks.

    Args:
        bundle_path (str): The path or identifier of the Apigee proxy bundle to test.
        api_spec_path (Optional[str]): Path to an OpenAPI/Swagger specification for validation.
        environment (str): The target environment for testing (e.g., "dev", "test", "prod").

    Returns:
        str: A JSON string summarizing the test results, including status, findings, and recommendations.
    """
    print(f"Simulating testing for Apigee proxy bundle: {bundle_path} in environment: {environment}")
    print(f"API Spec path provided: {api_spec_path if api_spec_path else 'None'}")

    # Simulate various test outcomes
    functional_status = "PASS" if random.random() > 0.1 else "FAIL"
    performance_status = "PASS" if random.random() > 0.2 else "DEGRADED"
    security_status = "PASS" if random.random() > 0.3 else "VULNERABILITIES_FOUND"

    findings = []
    recommendations = []

    if functional_status == "FAIL":
        findings.append("Functional test failed: Endpoint '/v1/users' returned 500 error.")
        recommendations.append("Review target endpoint configuration and backend service health.")
    if performance_status == "DEGRADED":
        findings.append("Performance degraded: Average response time increased by 30% under load.")
        recommendations.append("Optimize policies, consider caching, or scale backend resources.")
    if security_status == "VULNERABILITIES_FOUND":
        findings.append("Security vulnerability: Exposed API key in response header for '/v1/admin'.")
        recommendations.append("Implement response masking policy for sensitive data.")
    
    if api_spec_path:
        if random.random() < 0.2:
            findings.append(f"API spec mismatch: Response for '/v1/products' does not conform to OpenAPI schema from {api_spec_path}.")
            recommendations.append("Update API proxy response policies or OpenAPI specification.")

    summary = {
        "proxy_bundle": bundle_path,
        "environment": environment,
        "overall_status": "FAIL" if any(s != "PASS" for s in [functional_status, performance_status, security_status]) else "PASS",
        "functional_test": {"status": functional_status, "details": "All critical paths tested."},
        "performance_test": {"status": performance_status, "details": "Load test with 100 concurrent users for 60s."},
        "security_scan": {"status": security_status, "details": "OWASP Top 10 checks performed."},
        "findings": findings if findings else ["No critical issues found."],
        "recommendations": recommendations if recommendations else ["Proxy bundle appears stable and secure."],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    return json.dumps(summary, indent=2)

@tool
def get_apigee_proxy_details(proxy_name: str, organization: str, environment: str) -> str:
    """
    Simulates fetching details of an Apigee proxy using the Apigee Management APIs.

    Args:
        proxy_name (str): The name of the Apigee proxy.
        organization (str): The Apigee organization the proxy belongs to.
        environment (str): The environment where the proxy is deployed.

    Returns:
        str: A JSON string containing simulated proxy details.
    """
    print(f"Simulating fetching details for proxy: {proxy_name} in org: {organization}, env: {environment}")
    
    # Simulate different proxy configurations
    if "secure" in proxy_name.lower():
        policies = ["APIKeyVerification", "OAuthV2", "JSONThreatProtection"]
        target_url = "https://secure-backend.example.com"
    elif "public" in proxy_name.lower():
        policies = ["Quota", "SpikeArrest"]
        target_url = "https://public-api.example.com"
    else:
        policies = ["VerifyAPIKey"]
        target_url = "https://default-backend.example.com"

    details = {
        "proxy_name": proxy_name,
        "organization": organization,
        "environment": environment,
        "base_path": f"/{proxy_name}/v1",
        "target_endpoint": target_url,
        "deployed_revision": random.randint(1, 15),
        "policies_attached": policies,
        "virtual_hosts": ["default", "secure"],
        "last_modified": datetime.utcnow().isoformat() + "Z"
    }
    return json.dumps(details, indent=2)

@tool
def analyze_api_specification(spec_content: str) -> str:
    """
    Parses an OpenAPI/Swagger specification to extract key information like endpoints,
    methods, and schemas.

    Args:
        spec_content (str): The content of the OpenAPI/Swagger specification (JSON or YAML).

    Returns:
        str: A JSON string summarizing the parsed API specification.
    """
    print("Simulating analysis of API specification content.")
    try:
        # Basic simulation of parsing - in a real scenario, use a library like `openapi-spec-validator`
        # or `pyyaml` for YAML.
        spec = json.loads(spec_content)
        
        endpoints = []
        schemas = {}

        if 'paths' in spec:
            for path, methods in spec['paths'].items():
                for method, details in methods.items():
                    endpoints.append({
                        "path": path,
                        "method": method.upper(),
                        "summary": details.get('summary', ''),
                        "operation_id": details.get('operationId', '')
                    })
        
        if 'components' in spec and 'schemas' in spec['components']:
            schemas = spec['components']['schemas']

        summary = {
            "title": spec.get('info', {}).get('title', 'Untitled API'),
            "version": spec.get('info', {}).get('version', '1.0.0'),
            "base_path": spec.get('servers', [{}])[0].get('url', '/'),
            "total_endpoints": len(endpoints),
            "endpoints": endpoints,
            "schemas_defined": list(schemas.keys())
        }
        return json.dumps(summary, indent=2)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON API specification content provided."}, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to analyze API specification: {str(e)}"}, indent=2)

@tool
def generate_synthetic_test_data(schema_json: str, count: int = 1) -> str:
    """
    Generates synthetic JSON test data based on a provided JSON schema.
    This is a simplified generator for demonstration.

    Args:
        schema_json (str): A JSON string representing the schema for data generation.
        count (int): The number of data objects to generate.

    Returns:
        str: A JSON string containing an array of generated data objects.
    """
    print(f"Simulating synthetic test data generation for schema: {schema_json}, count: {count}")
    try:
        schema = json.loads(schema_json)
        generated_data = []

        def generate_value(prop_schema):
            prop_type = prop_schema.get("type")
            if prop_type == "string":
                if "enum" in prop_schema:
                    return random.choice(prop_schema["enum"])
                return ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 15)))
            elif prop_type == "integer":
                return random.randint(prop_schema.get("minimum", 1), prop_schema.get("maximum", 100))
            elif prop_type == "boolean":
                return random.choice([True, False])
            elif prop_type == "array":
                item_schema = prop_schema.get("items", {"type": "string"})
                return [generate_value(item_schema) for _ in range(random.randint(1, 3))]
            elif prop_type == "object":
                obj = {}
                for sub_prop, sub_schema in prop_schema.get("properties", {}).items():
                    obj[sub_prop] = generate_value(sub_schema)
                return obj
            return None

        for _ in range(count):
            data_object = {}
            if "properties" in schema:
                for prop, prop_schema in schema["properties"].items():
                    data_object[prop] = generate_value(prop_schema)
            generated_data.append(data_object)
        
        return json.dumps(generated_data, indent=2)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON schema provided."}, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to generate synthetic data: {str(e)}"}, indent=2)

@tool
def simulate_load_test(proxy_url: str, duration_seconds: int, users: int) -> str:
    """
    Simulates a load test against a given API proxy URL.

    Args:
        proxy_url (str): The URL of the Apigee proxy endpoint to test.
        duration_seconds (int): The duration of the load test in seconds.
        users (int): The number of concurrent virtual users to simulate.

    Returns:
        str: A JSON string containing simulated load test metrics.
    """
    print(f"Simulating load test for {proxy_url} with {users} users for {duration_seconds} seconds.")
    
    # Simulate performance metrics
    avg_response_time = round(random.uniform(50, 500), 2) # ms
    p90_response_time = round(avg_response_time * random.uniform(1.2, 1.8), 2)
    requests_per_second = round(random.uniform(users * 0.5, users * 1.5), 2)
    error_rate = round(random.uniform(0, 5), 2) # percentage

    status = "PASS"
    if avg_response_time > 300 or error_rate > 1:
        status = "FAIL"
    elif avg_response_time > 150:
        status = "WARNING"

    metrics = {
        "target_url": proxy_url,
        "duration_seconds": duration_seconds,
        "concurrent_users": users,
        "overall_status": status,
        "average_response_time_ms": avg_response_time,
        "p90_response_time_ms": p90_response_time,
        "requests_per_second": requests_per_second,
        "total_requests": int(requests_per_second * duration_seconds),
        "error_rate_percent": error_rate,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    return json.dumps(metrics, indent=2)

@tool
def scan_for_security_vulnerabilities(proxy_url: str) -> str:
    """
    Simulates a security scan for common vulnerabilities on an Apigee proxy endpoint.

    Args:
        proxy_url (str): The URL of the Apigee proxy endpoint to scan.

    Returns:
        str: A JSON string detailing simulated security findings.
    """
    print(f"Simulating security scan for {proxy_url}.")
    
    vulnerabilities = []
    if random.random() < 0.3:
        vulnerabilities.append({
            "severity": "HIGH",
            "type": "API Key Exposure",
            "description": "API key found in response body or header, potentially exposing backend access.",
            "recommendation": "Implement response masking or ensure API keys are not returned to clients."
        })
    if random.random() < 0.2:
        vulnerabilities.append({
            "severity": "MEDIUM",
            "