locals {
  data_lake_bucket = "dtc_data_lake"
}

variable "project" {
  description = "dtc-de-zoomcamp-project"
}

variable "region" {
  description = "Region for GCP resources. Choose as per your location: https://cloud.google.com/about/locations"
  default = "europe-west2"
  type = string
}

variable "bucket_name" {
  description = "The name of the GCS bucket. Must be globally unique."
  default = "dtc_de_project"
}

variable "storage_class" {
  description = "Storage class type for your bucket. Check official docs for more info."
  default = "STANDARD"
}

variable "BQ_DATASET" {
  description = "BigQuery Dataset that raw data (from GCS) will be written to"
  type = string
  default = "train_movements"
}

variable "credentials" {
  description = "Use this if you do not want to set env-var GOOGLE_APPLICATION_CREDENTIALS"
  type = string
  default = "/Users/ywang/.gcp/dtc-de-project-380810-2f9e017ffb97.json"
}