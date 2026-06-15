{{/* Common name + labels helpers */}}

{{- define "platform.name" -}}
ai-agent-platform
{{- end -}}

{{- define "platform.labels" -}}
app.kubernetes.io/name: {{ include "platform.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "platform.namespace" -}}
{{ .Values.global.namespace }}
{{- end -}}

{{/* Async + sync database URLs derived from secret values */}}
{{- define "platform.databaseUrl" -}}
postgresql+asyncpg://{{ .Values.secrets.postgresUser }}:{{ .Values.secrets.postgresPassword }}@postgres-service:{{ .Values.postgres.port }}/{{ .Values.secrets.postgresDb }}
{{- end -}}

{{- define "platform.databaseUrlSync" -}}
postgresql://{{ .Values.secrets.postgresUser }}:{{ .Values.secrets.postgresPassword }}@postgres-service:{{ .Values.postgres.port }}/{{ .Values.secrets.postgresDb }}
{{- end -}}
