"""
Helper functions for path manipulation in tests.
"""
import os


def create_mock_path_join(target_path):
    """Create a mock function for os.path.join that intercepts specific calls.
    
    This is useful for testing code that uses os.path.join with specific arguments.
    
    Args:
        target_path: The path to return when the expected arguments are matched
    
    Returns:
        function: A mock join function that returns target_path for ('data', 'players.json')
                  and calls the real os.path.join for other arguments
    """
    original_join = os.path.join
    
    def mock_join(*args):
        if len(args) == 2 and args[0] == 'data' and args[1] == 'players.json':
            return target_path
        return original_join(*args)
    
    return mock_join

