# Usage

## Reverse Proxy and Load Balancer

- We will use a [Dozzle](https://dozzle.dev/) as our example. Its `docker-compose.yml` from
  its [website](https://dozzle.dev/guide/getting-started#standalone-docker) is something like this:

    ```yaml
    services:
        dozzle:
            image: amir20/dozzle:latest
            volumes:
                - /var/run/docker.sock:/var/run/docker.sock
            ports:
                - 8080:8080
    ```

  To use it as a reverse proxy or a load balancer endpoint, add the `fpm-network` docker network to the dozzle
  container:

    ```yaml
    services:
        dozzle:
            image: amir20/dozzle:latest
            volumes:
                - /var/run/docker.sock:/var/run/docker.sock
            networks:
                - fpm-network

    networks:
        fpm-network:
            external: true
    ```

  Notice that the `fpm-network` is defined in the `docker-compose.yml` file. This is the same network defined in the [
  docker-compose.yml](./../docker-compose.yml) file.

  We also removed the `ports` section from the `dozzle` container. This is because our `ferron` service in
  the [docker-compose.yml](./../docker-compose.yml) is connected to the `dozzle` service via the `fpm-network` network.
  Now you can create a reverse proxy by using `http://dozzle:8080` as the backend URL in the Ferron Proxy Manager web
  UI.

  A screenshot of the Ferron Proxy Manager web UI with the necessary configuration for a reverse proxy is shown below:

  ![Usage for Reverse Proxy](./../screenshots/usage_reverse_proxy.png)

  You can use the same backend url for a load balancer.

- For docker compose files with multiple services, attach the `fpm-network` to the service that you want to
  connect to the reverse proxy or load balancer. This is typically the service which exposes a web UI or the one which
  you want to be publicly accessible.