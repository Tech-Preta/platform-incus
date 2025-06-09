deployment:
  replicas: 3

podDisruptionBudget:
  enabled: true
  minAvailable: 1

ingressClass:
  enabled: true
  name: "traefik"
  isDefaultClass: true

providers:
  kubernetesCRD:
    enabled: true
  kubernetesIngress:
    enabled: true
  kubernetesGateway:
    enabled: false

metrics:
  addInternals: false
  prometheus:
    entryPoint: metrics
    addEntryPointsLabels: false
    addRoutersLabels: false
    addServicesLabels: false
    buckets: ""
    manualRouting: false
    headerLabels: {}
    service:
      enabled: false
      labels: {}
      annotations: {}
    disableAPICheck: false
    serviceMonitor:
      enabled: false
      metricRelabelings: []
      relabelings: []
      jobLabel: ""
      interval: ""
      honorLabels: false
      scrapeTimeout: ""
      honorTimestamps: false
      enableHttp2: false
      followRedirects: false
      additionalLabels: {}
      namespace: ""
      namespaceSelector: {}
    prometheusRule:
      enabled: false
      additionalLabels: {}
      namespace: ""
  otlp:
    enabled: false
    addEntryPointsLabels: false
    addRoutersLabels: false
    addServicesLabels: false
    explicitBoundaries: []
    pushInterval: ""
    http:
      enabled: false
      endpoint: ""
      headers: {}
      tls:
        ca: ""
        cert: ""
        key: ""
        insecureSkipVerify: false
    grpc:
      enabled: false
      endpoint: ""
      insecure: false
      tls:
        ca: ""
        cert: ""
        key: ""
        insecureSkipVerify: false

globalArguments:
  - "--global.checknewversion"
  - "--global.sendanonymoususage"

additionalArguments:
  - "--api.dashboard=true"
  - "--api.insecure=true"
env: []
envFrom: []

ports:
  traefik:
    port: 8080
    expose:
      default: false
    exposedPort: 8080
    protocol: TCP
  web:
    port: 80
    expose:
      default: true
    exposedPort: 80
    protocol: TCP
  websecure:
    port: 443
    expose:
      default: true
    exposedPort: 443
    protocol: TCP
    tls:
      enabled: true
      options: ""
      certResolver: ""
      domains: []
    middlewares: []
  metrics:
    port: 9100
    expose:
      default: false
    exposedPort: 9100
    protocol: TCP

tlsOptions: {}
tlsStore: {}

service:
  enabled: true
  single: true
  type: LoadBalancer
  annotations: {}
  annotationsTCP: {}
  annotationsUDP: {}
  labels: {}
  spec:
    loadBalancerIP: "${load_balancer_ip}"

autoscaling:
  enabled: false

certificatesResolvers: {}