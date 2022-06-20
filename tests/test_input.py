import time

import pytest

from manage_lists.filter_list import remove_skipped_idx, get_only_idx
from study_info.get_sra_study_info import get_retmax, get_id_list, get_run_uid_by_id


class TestInputESEARCHParams:

    # *******************************************************************************************************
    # Test list 1
    # *******************************************************************************************************

    # To get max count of runs in the study from SRA database. Correct term (SRA study identifier) was send.
    def test_get_ret_max_correct_term(self):
        assert (get_retmax('SRP150545') == 6)

    def test_get_ret_max_correct_term_2(self):
        time.sleep(1)
        assert (get_retmax('SRP163674') == 129)

    def test_get_ret_max_correct_term_3(self):
        # To check identifiers can there https://www.ncbi.nlm.nih.gov/sra/?term=40
        # It's strange: there are 4 runs in the SRA study with uid 40, but sra database return 1
        time.sleep(1)
        assert (get_retmax('40') == 1)

    # To get max count of runs in the study from SRA database. Incorrect term (SRA study identifier) was send.
    def test_get_ret_max_incorrect_term(self):
        time.sleep(1)
        assert (get_retmax('SRP16367434shhhh4') == 0)

    # To get max count of runs in the study from SRA database. Incorrect term (SRA study identifier) was send.
    def test_get_ret_max_incorrect_term_2(self):
        time.sleep(1)
        assert (get_retmax('1') == 0)

    # *******************************************************************************************************
    # Test list 2
    # *******************************************************************************************************

    # To get the list of run idx which were received by SRA Study identifier
    # and retmax parameters (max cnt of runs in study)

    # Correct term AND correct retmax
    def test_get_id_list_correct(self):
        time.sleep(1)
        assert (get_id_list(
            term='SRP150545',
            retmax=6
        ) == ['5704372', '5704371', '5704370', '5704369', '5704368', '5704367'])

    # Correct term AND INcorrect retmax (more than accessed) - it's normal situation
    def test_get_id_list_correct_2(self):
        time.sleep(1)
        assert (get_id_list(
            term='SRP150545',
            retmax=60
        ) == ['5704372', '5704371', '5704370', '5704369', '5704368', '5704367'])

    # Correct term AND INcorrect retmax (less than accessed) - it's normal situation (we will receive less idx)
    def test_get_id_list_correct_3(self):
        time.sleep(1)
        assert (get_id_list(
            term='SRP150545',
            retmax=2
        ) == ['5704372', '5704371'])

    # InCorrect term  - it's wrong situation
    def test_get_id_list_incorrect(self):
        time.sleep(1)
        with pytest.raises(SystemExit):
            get_id_list(
                term='SRP150545efrghty',
                retmax=60)


class TestInputEFETCHParams:

    # Get the Run parameters by its Id through efetch service

    # Test get function with correct input parameters
    def test_get_run_uid_by_id_correct(self):
        time.sleep(1)
        assert get_run_uid_by_id(
            id=5704372
        ) == {
            'accession': 'SRR7343998',
            'alias': 'SE3A_S9_R1_001.fastq.gz',
            'cluster_name': 'public',
            'is_public': 'true',
            'load_done': 'true',
            'published': '2018-06-14 21:22:14',
            'size': '11190505425',
            'static_data_available': '1',
            'total_bases': '24231063431',
            'total_spots': '80887417'
        }

    # Test get function with incorrect input parameters or with the UID where RUN tag is absent
    def test_get_run_uid_by_id_incorrect(self):
        time.sleep(1)
        with pytest.raises(SystemExit):
            get_run_uid_by_id(id='abababa')


class TestFilterAccessionLists:

    #  To test functions which filter an accession list by including or excluding run names

    def test_remove_skipped_idx_1(self):
        assert set(remove_skipped_idx(
            total_list=['SRR7343998', 'SRR7343999', 'SRR7344000'],
            skip_list=['SRR7343997']
        )) == {'SRR7343998', 'SRR7343999', 'SRR7344000'}

    def test_remove_skipped_idx_2(self):
        assert set(remove_skipped_idx(
            total_list=['SRR7343998', 'SRR7343999', 'SRR7344000'],
            skip_list=['SRR7343999'])
        ) == {'SRR7343998', 'SRR7344000'}

    def test_remove_skipped_idx_3(self):
        assert remove_skipped_idx(
            total_list=['SRR7343998', 'SRR7343999', 'SRR7344000']
        ) == ['SRR7343998', 'SRR7343999', 'SRR7344000']

    def test_get_only_idx_1(self):
        f_return = get_only_idx(
            total_list=['SRR7343998', 'SRR7343999', 'SRR7344000'],
            only_list=['SRR7343999', 'SRR7344000']
        )
        assert set(f_return) == {'SRR7343999', 'SRR7344000'}

    def test_get_only_idx_2(self):
        f_return = get_only_idx(
            total_list=['SRR7343998', 'SRR7343999', 'SRR7344000'],
            only_list=['SRR73439aa', 'SRR7344000']
        )
        assert set(f_return) == {'SRR7344000'}

    def test_get_only_idx_3(self):
        f_return = get_only_idx(
            total_list=['SRR7343998', 'SRR7343999', 'SRR7344000'],
            only_list=['aaa', 'SR', 'ghgh']
        )
        assert f_return == []

    def test_get_only_idx_4(self):
        f_return = get_only_idx(
            total_list=['SRR7343998', 'SRR7343999', 'SRR7344000'],
            only_list=[]
        )
        assert f_return == ['SRR7343998', 'SRR7343999', 'SRR7344000']

    def test_get_only_idx_5(self):
        f_return = get_only_idx(total_list=['SRR7343998', 'SRR7343999', 'SRR7344000'])
        assert f_return == ['SRR7343998', 'SRR7343999', 'SRR7344000']
