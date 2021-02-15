import logging


def remove_skipped_idx(total_list, skip_list=None):
    """
    Remove idx of Runs which must be skipped

    Parameters
    ----------
    total_list: list of str
    skip_list: list of str

    Returns
    -------
        list of str
    """
    if skip_list is None:
        skip_list = []

    if skip_list != []:

        logging.debug('Total list: {}'.format(total_list))
        logging.debug('Skip list: {}'.format(skip_list))

        rest = list(set(total_list) - set(skip_list))
        logging.info('List of runs without skipped: {}'.format(rest))

    else:
        logging.debug('Nothing to skip')
        rest = total_list
    return rest


def get_only_idx(total_list, only_list=None):
    """
    Return list of idx from total_idx AND only_idx

    Parameters
    ----------
    total_list:  list of str
    only_list:  list of str

    Returns
    -------
         list of str
    """
    if only_list is None:
        only_list = []

    if only_list != []:

        diff = list(set(only_list) - set(total_list))

        if len(diff) == 0:
            logging.debug('Diff list is empty. Get whole only list')
            rest = only_list
        else:
            logging.info('Next names of Runs in the only-list is not in total Run list. They will be skipped')
            logging.info('  -- {}'.format(diff))
            rest = list(set(only_list) - set(diff))
    else:
        rest = total_list

    return rest
