def call(Map config = [:]) {
    def tools = config.get('tools', ['python', 'kaniko', 'git'])
    
    String yaml = """
apiVersion: v1
kind: Pod
spec:
  containers:
"""
    tools.each { tool ->
        yaml += libraryResource("pod-templates/${tool}.yaml")
        yaml += "\n"
    }
    
    return yaml
}