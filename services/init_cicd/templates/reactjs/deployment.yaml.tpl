apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ app_name }}
  labels:
    app: {{ app_name }}
spec:
  replicas: {{ replicas }}
  selector:
    matchLabels:
      app: {{ app_name }}
  template:
    metadata:
      labels:
        app: {{ app_name }}
    spec:
      serviceAccountName: {{ app_name }}-sa
      containers:
        - name: {{ app_name }}
          image: {{ image_repository }}:{{ image_tag }}
          ports:
            - containerPort: {{ container_port }}
          readinessProbe:
            httpGet:
              path: /
              port: {{ container_port }}
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /
              port: {{ container_port }}
            initialDelaySeconds: 10
            periodSeconds: 20
          resources:
            requests:
              cpu: {{ cpu_request }}
              memory: {{ memory_request }}
            limits:
              memory: {{ memory_limit }}
