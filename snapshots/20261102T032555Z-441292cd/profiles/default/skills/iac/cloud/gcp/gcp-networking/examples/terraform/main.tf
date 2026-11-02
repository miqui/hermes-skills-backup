terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

variable "project_id" { type = string }
variable "region" {
  type    = string
  default = "us-central1"
}

# Custom-mode VPC: no auto subnets, you own the IP plan.
resource "google_compute_network" "vpc" {
  project                 = var.project_id
  name                    = "app-vpc"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

# Subnet with Private Google Access + flow logs.
resource "google_compute_subnetwork" "app" {
  project                  = var.project_id
  name                     = "app-${var.region}"
  region                   = var.region
  network                  = google_compute_network.vpc.id
  ip_cidr_range            = "10.10.0.0/24"
  private_ip_google_access = true

  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

# Cloud NAT for VMs without external IPs.
resource "google_compute_router" "router" {
  project = var.project_id
  name    = "app-router"
  region  = var.region
  network = google_compute_network.vpc.id
}

resource "google_compute_router_nat" "nat" {
  project                            = var.project_id
  name                               = "app-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Service account used as firewall target/source identity.
resource "google_service_account" "web" {
  project      = var.project_id
  account_id   = "web-tier-sa"
  display_name = "web tier"
}

resource "google_service_account" "db" {
  project      = var.project_id
  account_id   = "db-tier-sa"
  display_name = "db tier"
}

# Allow IAP SSH (35.235.240.0/20) to tagged VMs.
resource "google_compute_firewall" "iap_ssh" {
  project   = var.project_id
  name      = "allow-iap-ssh"
  network   = google_compute_network.vpc.name
  direction = "INGRESS"
  priority  = 1000
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["ssh-iap"]
}

# Service-account-scoped rule: only web-sa -> db-sa on 5432.
# (Tags and service accounts cannot be mixed in one rule.)
resource "google_compute_firewall" "web_to_db" {
  project                 = var.project_id
  name                    = "allow-web-to-db"
  network                 = google_compute_network.vpc.name
  direction               = "INGRESS"
  priority                = 1000
  source_service_accounts = [google_service_account.web.email]
  target_service_accounts = [google_service_account.db.email]
  allow {
    protocol = "tcp"
    ports    = ["5432"]
  }
}

# Private Service Connect endpoint to Google APIs (all-apis bundle).
resource "google_compute_global_address" "psc_apis" {
  project      = var.project_id
  name         = "psc-apis-ip"
  purpose      = "PRIVATE_SERVICE_CONNECT"
  address_type = "INTERNAL"
  address      = "10.10.255.1"
  network      = google_compute_network.vpc.id
}

resource "google_compute_global_forwarding_rule" "psc_apis" {
  project = var.project_id
  # Name must be <= 20 chars, lowercase letters+digits only for Google APIs endpoints.
  name                  = "pscapis"
  network               = google_compute_network.vpc.id
  ip_address            = google_compute_global_address.psc_apis.id
  target                = "all-apis"
  load_balancing_scheme = ""
}

# Private Cloud DNS zone visible to the VPC.
resource "google_dns_managed_zone" "internal" {
  project    = var.project_id
  name       = "corp-internal"
  dns_name   = "corp.internal."
  visibility = "private"
  private_visibility_config {
    networks {
      network_url = google_compute_network.vpc.id
    }
  }
}

resource "google_dns_record_set" "db" {
  project      = var.project_id
  managed_zone = google_dns_managed_zone.internal.name
  name         = "db.corp.internal."
  type         = "A"
  ttl          = 300
  rrdatas      = ["10.10.0.10"]
}

# Shared VPC: run in the HOST project (needs compute.xpnAdmin at org/folder).
variable "service_project_id" {
  type    = string
  default = "my-service-project"
}

resource "google_compute_shared_vpc_host_project" "host" {
  project = var.project_id
}

resource "google_compute_shared_vpc_service_project" "svc" {
  host_project    = google_compute_shared_vpc_host_project.host.project
  service_project = var.service_project_id
}

# Per-subnet grant so service-project users can attach VMs to the subnet.
resource "google_compute_subnetwork_iam_member" "svc_user" {
  project    = var.project_id
  region     = var.region
  subnetwork = google_compute_subnetwork.app.name
  role       = "roles/compute.networkUser"
  member     = "group:app-team@example.com"
}
