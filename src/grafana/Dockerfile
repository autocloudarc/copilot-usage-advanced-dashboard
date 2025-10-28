FROM grafana/grafana-oss:11.4.4

USER root

# Install dependencies
RUN apk update && \
    apk add --no-cache libcap && \
    rm -rf /var/cache/apk/*

RUN setcap 'cap_net_bind_service=+ep' /usr/share/grafana/bin/grafana-server

# Switch back to grafana user
USER grafana

# Expose the Grafana port
EXPOSE 3000

# Start Grafana
CMD ["grafana-server"]