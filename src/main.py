import argparse
import json

import yaml

from destinations import YamlDestinationRepository
from route_service import calculate_route, render_route


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--waypoints", default="data/waypoints.yaml")
    parser.add_argument("--destinations", default="data/destinations.yaml")
    return parser.parse_args()


def main():
    args = parse_args()
    with open(args.config, encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    with open(args.waypoints, encoding="utf-8") as stream:
        plan = yaml.safe_load(stream)
    result = calculate_route(plan, YamlDestinationRepository(args.destinations), config)
    print("Route result:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("Route data returned from backend:")
    rendered = render_route(result, config)
    print(rendered if isinstance(rendered, str) else json.dumps(rendered, ensure_ascii=False))


if __name__ == "__main__":
    main()
