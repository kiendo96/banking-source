def call(Map config = [:]) {
    def tools = config.get('tools', ['python', 'kaniko', 'git'])
    
    String yaml = """
apiVersion: v1
kind: Pod
spec:
  hostAliases:
  - ip: "192.168.56.200"
    hostnames:
    - "harbor.local"
  containers:
"""
    tools.each { tool ->
        yaml += libraryResource("pod-templates/${tool}.yaml")
        yaml += "\n"
    }     
    return yaml
}