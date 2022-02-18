import time
import json

import pytest
from study_info.get_sra_study_info import (
    get_full_metadata, get_run_uid_with_no_exception,
    get_run_uid_with_only_list, get_run_uid_with_skipped_list,
    get_run_uid_with_total_list, get_total_spots_with_only_list,
    get_webenv_and_query_key_with_skipped_list,
    get_webenv_and_query_key_with_total_list)


class TestInputESEARCH_EFETCHParams:

    # Test get_run_uid_with_no_exception function with correct input parameters
    def test_get_run_uid_with_no_exception_with_total_list(self):
        time.sleep(1)
        webenv, query_key = get_webenv_and_query_key_with_total_list(
                        "SRP163674")
        SRRs, total_spots = get_run_uid_with_no_exception(webenv, query_key)
        assert (len(SRRs), len(total_spots)) == (129, 129)

    # Test get_webenv_and_query_key_with_total_list function with incorrect input parameters
    def test_get_webenv_and_query_key_with_total_list_incorrect(self):
        time.sleep(1)
        with pytest.raises(SystemExit):
            get_webenv_and_query_key_with_total_list(
                        "ahethaerhatef")

    # Test get_run_uid_with_no_exception function with correct input parameters
    def test_get_run_uid_with_no_exception_with_skipped_list(self):
        time.sleep(1)
        webenv, query_key = get_webenv_and_query_key_with_skipped_list(
                        "SRP163674", ['SRR7969880', 'SRR7969881', 'SRR7969882', 'SRR7969883'])
        SRRs, total_spots = get_run_uid_with_no_exception(webenv, query_key)
        assert (len(SRRs), len(total_spots)) == (125, 125)

    # Test get_webenv_and_query_key_with_skipped_list function with incorrect input parameters
    def test_get_webenv_and_query_key_with_skipped_list_incorrect(self):
        time.sleep(1)
        with pytest.raises(SystemExit):
            get_webenv_and_query_key_with_skipped_list(
                        "bazhreahbre", ['SRR7969880', 'SRR7969881', 'SRR7969882', 'SRR7969883'])

    # Test get_run_uid_with_only_list function with correct input parameters
    def test_get_run_uid_with_only_list(self):
        time.sleep(1)
        assert get_run_uid_with_only_list(
            only_list=['SRR7969880', 'SRR7969881', 'SRR7969882', 'SRR7969883']
        ) == (['SRR7969880', 'SRR7969881', 'SRR7969882', 'SRR7969883'], [50623, 29433, 36017, 20063])

    # Test get_run_uid_with_only_list function with incorrect input parameters
    def test_get_run_uid_with_only_list_incorrect(self):
        time.sleep(1)
        assert get_run_uid_with_only_list(
            only_list=['agarhaerhbefd', 'vhlhv l', 'SRR7969882', 'SRR7969883']
        ) == (['SRR7969882', 'SRR7969883'], [36017, 20063])


class TestENADataRetriaval:

    # Test get_run_uid_with_total_list function with correct input parameters
    def test_get_run_uid_with_total_list(self):
        SRRs, total_spots = get_run_uid_with_total_list("SRP163674", "q")
        assert (len(SRRs), len(total_spots)) == (129, 129)

    # Test get_run_uid_with_total_list function with incorrect input parameters
    def test_get_run_uid_with_total_list_incorrect(self):
        with pytest.raises(json.decoder.JSONDecodeError):
            get_run_uid_with_total_list("bhrhbaregbr", "q")

    # Test get_run_uid_with_skipped_list function with correct input parameters
    # Method is q, whic is used for fasterq_dump
    def test_get_run_uid_with_skipped_list_with_q_method(self):
        time.sleep(1)
        SRRs, total_spots = get_run_uid_with_skipped_list(
                                                    "SRP163674", ['SRR7969880', 'SRR7969881', 'SRR7969882', 'SRR7969883'], "q")
        assert (len(SRRs), len(total_spots)) == (125, 125)

    # Test get_run_uid_with_skipped_list function with incorrect input parameters
    # Method is q, whic is used for fasterq_dump
    def test_get_run_uid_with_skipped_list_with_q_method_incorrect(self):
        time.sleep(1)
        with pytest.raises(json.decoder.JSONDecodeError):
            get_run_uid_with_skipped_list("afvsdgvsegvd",
                                          ['SRR7969880', 'SRR7969881', 'SRR7969882', 'SRR7969883'], "q")

    # Test get_run_uid_with_skipped_list function with correct input parameters
    # Method is f/a, whic is used for FTP/Aspera
    def test_get_run_uid_with_skipped_list_without_q_method(self):
        time.sleep(1)
        SRRs, total_spots = get_run_uid_with_skipped_list(
                                                    "SRP163674", ['SRR7969880', 'SRR7969881', 'SRR7969882', 'SRR7969883'], "f")
        assert (len(SRRs), len(total_spots)) == (125, 0)

    # Test get_run_uid_with_skipped_list function with incorrect input parameters
    # Method is f/a, whic is used for FTP/Aspera
    def test_get_run_uid_with_skipped_list_without_q_method_incorrect(self):
        time.sleep(1)
        with pytest.raises(json.decoder.JSONDecodeError):
            get_run_uid_with_skipped_list("afvsdgvsegvd", ['SRR7969880', 'SRR7969881', 'SRR7969882', 'SRR7969883'], "f")

    # Test get_total_spots_with_only_list function with correct input parameters
    def test_get_total_spots_with_only_list(self):
        time.sleep(1)
        mock_total_spots = [50623, 29433, 36017, 20063]
        total_spots = get_total_spots_with_only_list(['SRR7969880', 'SRR7969881', 'SRR7969882', 'SRR7969883'])
        assert mock_total_spots == total_spots

    # Test get_total_spots_with_only_list function with incorrect input parameters
    def test_get_total_spots_with_only_list_incorrect(self):
        time.sleep(1)
        assert get_total_spots_with_only_list(['gasgweagveasdv', 'SRR7969881', 'SRR7969882', 'SRR7969883']) == []

    # Test get_full_metadata function with correct input parameters
    def test_get_full_metadata(self):
        time.sleep(1)
        mock_metadata = [{'run_accession': 'SRR7969880', 'experiment_accession': 'SRX4803380', 'base_count': '22674621'}, {'run_accession': 'SRR7969881', 'experiment_accession': 'SRX4803379', 'base_count': '13180909'}, {'run_accession': 'SRR7969882', 'experiment_accession': 'SRX4803378', 'base_count': '16173418'}, {'run_accession': 'SRR7969883', 'experiment_accession': 'SRX4803377', 'base_count': '8993061'}]
        metadata = get_full_metadata(['SRR7969880', 'SRR7969881', 'SRR7969882', 'SRR7969883'], "experiment_accession,base_count")
        assert mock_metadata == metadata

    # Test get_full_metadata function with incorrect input parameters
    def test_get_full_metadata_incorrect(self):
        time.sleep(1)
        with pytest.raises(SystemExit):
            get_full_metadata(['ghf,ckck', 'SRR7969881', 'SRR7969882', 'SRR7969883'], "experiment_accession,  base_count")
