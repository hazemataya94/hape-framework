apiVersion: v1
kind: Service
metadata:
  name: {{ app_name }}
  labels:
    app: {{ app_name }}
spec:
  type: ClusterIP
  selector:
    app: {{ app_name }}
  ports:
    - protocol: TCP
      port: {{ service_port }}
      targetPort: {{ container_port }}
