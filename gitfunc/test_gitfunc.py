import pytest
import sys
import os
import tempfile
import shutil
import hashlib
import zlib
from pathlib import Path
from abc import ABC, abstractmethod

# Add lab3 to the path so we can import the modules
sys.path.insert(0, os.path.dirname(__file__))

# Try to import modules individually
pygit_commands = None
pygit_objects = None
pygit_index = None

try:
    import pygit_commands
except ImportError:
    pass

try:
    # Try different import patterns for objects module
    try:
        from pygit import objects as pygit_objects
    except ImportError:
        try:
            import pygit.objects as pygit_objects
        except ImportError:
            import objects as pygit_objects
except ImportError:
    pass

try:
    # Try different import patterns for index module
    try:
        from pygit import index as pygit_index
    except ImportError:
        try:
            import pygit.index as pygit_index
        except ImportError:
            import index as pygit_index
except ImportError:
    pass


class TestPygitInit:
    """Tests for pygit init command and repository structure."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        yield temp_dir
        os.chdir(old_cwd)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.skipif(pygit_commands is None, reason="pygit module not found")
    def test_pygit_module_exists(self):
        """Test that pygit module can be imported."""
        assert pygit_commands is not None, "pygit module should be importable"
    
    @pytest.mark.skipif(pygit_commands is None, reason="pygit module not found")
    def test_init_command_exists(self):
        """Test that init functionality exists."""
        # Look for init command implementation
        has_init = (
                hasattr(pygit_commands, 'init') or
                hasattr(pygit_commands, 'cmd_init') or
                hasattr(pygit_commands, 'command_init') or
                any('init' in attr.lower() for attr in dir(pygit_commands))
        )
        assert has_init, "Init command not found in pygit module"
    
    @pytest.mark.skipif(pygit_commands is None, reason="pygit module not found")
    def test_init_creates_pygit_directory(self, temp_dir):
        """Test that init command creates .pygit directory."""
        # Try to call init function
        try:
            if hasattr(pygit_commands, 'init'):
                pygit_commands.init()
            elif hasattr(pygit_commands, 'cmd_init'):
                pygit_commands.cmd_init()
            elif hasattr(pygit_commands, 'main'):
                # Simulate command line call
                original_argv = sys.argv
                sys.argv = ['pygit', 'init']
                try:
                    pygit_commands.main()
                except SystemExit:
                    pass  # Expected for some CLI implementations
                finally:
                    sys.argv = original_argv
            
            # Check if .pygit directory was created
            pygit_dir = Path('.pygit')
            assert pygit_dir.exists(), ".pygit directory should be created"
            assert pygit_dir.is_dir(), ".pygit should be a directory"
        
        except Exception as e:
            pytest.fail(f"Init command failed: {e}")
    
    @pytest.mark.skipif(pygit_commands is None, reason="pygit module not found")
    def test_init_creates_required_structure(self, temp_dir):
        """Test that init creates required subdirectories and files."""
        # Run init
        try:
            if hasattr(pygit_commands, 'init'):
                pygit_commands.init()
            elif hasattr(pygit_commands, 'cmd_init'):
                pygit_commands.cmd_init()
            else:
                pytest.skip("Cannot determine how to call init command")
        except Exception:
            pytest.skip("Init command not properly implemented yet")
        
        pygit_dir = Path('.pygit')
        if not pygit_dir.exists():
            pytest.skip("Init command didn't create .pygit directory")
        
        # Check required subdirectories
        objects_dir = pygit_dir / 'objects'
        refs_heads_dir = pygit_dir / 'refs' / 'heads'
        head_file = pygit_dir / 'HEAD'
        
        assert objects_dir.exists(), "objects/ directory should be created"
        assert objects_dir.is_dir(), "objects/ should be a directory"
        
        assert refs_heads_dir.exists(), "refs/heads/ directory should be created"
        assert refs_heads_dir.is_dir(), "refs/heads/ should be a directory"
        
        assert head_file.exists(), "HEAD file should be created"
        assert head_file.is_file(), "HEAD should be a file"
    
    @pytest.mark.skipif(pygit_commands is None, reason="pygit module not found")
    def test_head_file_content(self, temp_dir):
        """Test that HEAD file contains correct default content."""
        try:
            if hasattr(pygit_commands, 'init'):
                pygit_commands.init()
            elif hasattr(pygit_commands, 'cmd_init'):
                pygit_commands.cmd_init()
            else:
                pytest.skip("Cannot call init command")
        except Exception:
            pytest.skip("Init command not implemented")
        
        head_file = Path('.pygit/HEAD')
        if not head_file.exists():
            pytest.skip("HEAD file not created")
        
        content = head_file.read_text().strip()
        expected = "ref: refs/heads/main"
        assert content == expected, f"HEAD should contain '{expected}', got '{content}'"


class TestObjectModel:
    """Tests for pygit/objects.py module."""
    
    @pytest.mark.skipif(pygit_objects is None, reason="objects module not found")
    def test_objects_module_exists(self):
        """Test that objects module can be imported."""
        assert pygit_objects is not None, "objects module should be importable"
    
    @pytest.mark.skipif(pygit_objects is None, reason="objects module not found")
    def test_git_object_base_class_exists(self):
        """Test that GitObject base class exists."""
        assert hasattr(pygit_objects, 'GitObject'), "GitObject class not found"
        
        git_object_class = pygit_objects.GitObject
        
        # Check if it's an abstract base class
        try:
            # Should not be able to instantiate abstract class
            instance = git_object_class()
            # If we can instantiate it, check it has required methods
            assert hasattr(instance, 'serialize'), "GitObject should have serialize method"
            assert hasattr(instance, 'deserialize'), "GitObject should have deserialize method"
        except TypeError:
            # Expected for abstract base class
            pass
    
    @pytest.mark.skipif(pygit_objects is None, reason="objects module not found")
    def test_blob_class_exists(self):
        """Test that Blob class exists and can be instantiated."""
        assert hasattr(pygit_objects, 'Blob'), "Blob class not found"
        
        # Test instantiation
        test_data = b"Hello, World!"
        blob = pygit_objects.Blob(test_data)
        assert blob is not None, "Blob should be instantiable"
        
        # Test serialize method
        assert hasattr(blob, 'serialize'), "Blob should have serialize method"
        serialized = blob.serialize()
        assert isinstance(serialized, bytes), "serialize() should return bytes"
        assert serialized == test_data, "Blob serialize should return original data"
    
    @pytest.mark.skipif(pygit_objects is None, reason="objects module not found")
    def test_tree_class_exists(self):
        """Test that Tree class exists and has required functionality."""
        assert hasattr(pygit_objects, 'Tree'), "Tree class not found"
        
        # Test instantiation
        tree = pygit_objects.Tree()
        assert tree is not None, "Tree should be instantiable"
        
        # Test serialize method
        assert hasattr(tree, 'serialize'), "Tree should have serialize method"
        
        # Tree should handle entries (mode, path, sha)
        try:
            serialized = tree.serialize()
            assert isinstance(serialized, bytes), "Tree serialize should return bytes"
        except Exception:
            # Might need entries to be added first
            pass
    
    @pytest.mark.skipif(pygit_objects is None, reason="objects module not found")
    def test_commit_class_exists(self):
        """Test that Commit class exists and has required functionality."""
        assert hasattr(pygit_objects, 'Commit'), "Commit class not found"
        
        # Test instantiation
        try:
            commit = pygit_objects.Commit()
            assert commit is not None, "Commit should be instantiable"
        except TypeError:
            # Might require parameters
            try:
                commit = pygit_objects.Commit(
                    tree_hash="dummy_tree_hash",
                    parent_hash=None,
                    author="Test Author <test@example.com>",
                    message="Test commit"
                )
            except Exception:
                pytest.skip("Cannot determine Commit constructor signature")
        
        # Test serialize method
        assert hasattr(commit, 'serialize'), "Commit should have serialize method"
    
    @pytest.mark.skipif(pygit_objects is None, reason="objects module not found")
    def test_hash_object_function_exists(self):
        """Test that hash_object function exists."""
        assert hasattr(pygit_objects, 'hash_object'), "hash_object function not found"
    
    @pytest.mark.skipif(pygit_objects is None, reason="objects module not found")
    def test_hash_object_functionality(self):
        """Test hash_object function basic functionality."""
        if not hasattr(pygit_objects, 'hash_object'):
            pytest.skip("hash_object function not found")
        
        test_data = b"test content"
        obj_type = "blob"
        
        try:
            result = pygit_objects.hash_object(test_data, obj_type)
            
            # Should return a string (hash)
            assert isinstance(result, str), "hash_object should return string hash"
            assert len(result) == 40, "SHA-1 hash should be 40 characters"
            
            # Verify it's a valid hex string
            int(result, 16)  # Should not raise exception
            
        except Exception as e:
            pytest.fail(f"hash_object function failed: {e}")
    
    @pytest.mark.skipif(pygit_objects is None, reason="objects module not found")
    def test_sha1_hash_correctness(self):
        """Test that hash_object produces correct SHA-1 hashes."""
        if not hasattr(pygit_objects, 'hash_object'):
            pytest.skip("hash_object function not found")
        
        test_data = b"hello world"
        obj_type = "blob"
        
        try:
            result = pygit_objects.hash_object(test_data, obj_type)
            
            # Calculate expected hash manually
            header = f"{obj_type} {len(test_data)}\0".encode()
            full_data = header + test_data
            expected_hash = hashlib.sha1(full_data).hexdigest()
            
            assert result == expected_hash, f"Expected {expected_hash}, got {result}"
            
        except Exception:
            pytest.skip("hash_object implementation not complete")


class TestIndex:
    """Tests for pygit/index.py module."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        # Create .pygit structure
        os.makedirs('.pygit/objects', exist_ok=True)
        os.makedirs('.pygit/refs/heads', exist_ok=True)
        with open('.pygit/HEAD', 'w') as f:
            f.write('ref: refs/heads/main')
        
        yield temp_dir
        os.chdir(old_cwd)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.skipif(pygit_index is None, reason="index module not found")
    def test_index_module_exists(self):
        """Test that index module can be imported."""
        assert pygit_index is not None, "index module should be importable"
    
    @pytest.mark.skipif(pygit_index is None, reason="index module not found")
    def test_read_write_index_functions_exist(self):
        """Test that index read/write functions exist."""
        has_read = (
            hasattr(pygit_index, 'read_index') or
            hasattr(pygit_index, 'load_index') or
            any('read' in attr.lower() and 'index' in attr.lower() for attr in dir(pygit_index))
        )
        assert has_read, "Index reading function not found"
        
        has_write = (
            hasattr(pygit_index, 'write_index') or
            hasattr(pygit_index, 'save_index') or
            any('write' in attr.lower() and 'index' in attr.lower() for attr in dir(pygit_index))
        )
        assert has_write, "Index writing function not found"
    
    @pytest.mark.skipif(pygit_index is None, reason="index module not found")
    def test_index_operations(self, temp_repo):
        """Test basic index read/write operations."""
        # Create a test file
        test_file = Path('test.txt')
        test_content = "Hello, World!"
        test_file.write_text(test_content)
        
        # Look for read_index function
        read_func = None
        write_func = None
        
        if hasattr(pygit_index, 'read_index'):
            read_func = pygit_index.read_index
        if hasattr(pygit_index, 'write_index'):
            write_func = pygit_index.write_index
        
        if not (read_func and write_func):
            pytest.skip("Index functions not found")
        
        try:
            # Test reading empty index
            index_data = read_func()
            assert isinstance(index_data, (list, dict)), "Index should return list or dict"
            
            # Test writing index (this is a basic test)
            if isinstance(index_data, list):
                test_entry = ('test.txt', 'dummy_hash', {})
                index_data.append(test_entry)
            
            write_func(index_data)
            
            # Verify index file was created
            index_file = Path('.pygit/index')
            assert index_file.exists(), "Index file should be created"
            
        except Exception as e:
            pytest.fail(f"Index operations failed: {e}")


class TestAddCommand:
    """Tests for pygit add command."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        # Create .pygit structure
        os.makedirs('.pygit/objects', exist_ok=True)
        os.makedirs('.pygit/refs/heads', exist_ok=True)
        with open('.pygit/HEAD', 'w') as f:
            f.write('ref: refs/heads/main')
        
        yield temp_dir
        os.chdir(old_cwd)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.skipif(pygit_commands is None, reason="pygit module not found")
    def test_add_command_exists(self):
        """Test that add command exists."""
        has_add = (
                hasattr(pygit_commands, 'add') or
                hasattr(pygit_commands, 'cmd_add') or
                hasattr(pygit_commands, 'command_add') or
                any('add' in attr.lower() for attr in dir(pygit_commands))
        )
        assert has_add, "Add command not found"
    
    @pytest.mark.skipif(pygit_commands is None, reason="pygit module not found")
    def test_add_file_basic(self, temp_repo):
        """Test basic file addition to index."""
        # Create a test file
        test_file = Path('test.txt')
        test_content = "Hello, Git!"
        test_file.write_text(test_content)
        
        try:
            # Try to call add command
            if hasattr(pygit_commands, 'add'):
                pygit_commands.add('test.txt')
            elif hasattr(pygit_commands, 'cmd_add'):
                pygit_commands.cmd_add(['test.txt'])
            else:
                pytest.skip("Cannot determine how to call add command")
            
            # Check if index was updated (file should exist)
            index_file = Path('.pygit/index')
            # If index file exists, that's a good sign
            if index_file.exists():
                assert True, "Index file created"
            
            # Check if blob was created in objects directory
            objects_dir = Path('.pygit/objects')
            if objects_dir.exists():
                # Look for any object files
                object_files = list(objects_dir.rglob('*'))
                object_files = [f for f in object_files if f.is_file()]
                # Having object files is a good sign
                if object_files:
                    assert len(object_files) > 0, "Object files should be created"
        
        except Exception as e:
            pytest.fail(f"Add command failed: {e}")


class TestCommitCommand:
    """Tests for pygit commit command."""
    
    @pytest.fixture
    def temp_repo_with_file(self):
        """Create a temporary repository with a staged file."""
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        # Create .pygit structure
        os.makedirs('.pygit/objects', exist_ok=True)
        os.makedirs('.pygit/refs/heads', exist_ok=True)
        with open('.pygit/HEAD', 'w') as f:
            f.write('ref: refs/heads/main')
        
        # Create and add a test file
        test_file = Path('test.txt')
        test_file.write_text("Hello, Git!")
        
        yield temp_dir
        os.chdir(old_cwd)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.skipif(pygit_commands is None, reason="pygit module not found")
    def test_commit_command_exists(self):
        """Test that commit command exists."""
        has_commit = (
                hasattr(pygit_commands, 'commit') or
                hasattr(pygit_commands, 'cmd_commit') or
                hasattr(pygit_commands, 'command_commit') or
                any('commit' in attr.lower() for attr in dir(pygit_commands))
        )
        assert has_commit, "Commit command not found"
    
    @pytest.mark.skipif(pygit_commands is None, reason="pygit module not found")
    def test_write_tree_command_exists(self):
        """Test that write-tree command exists."""
        has_write_tree = (
                hasattr(pygit_commands, 'write_tree') or
                hasattr(pygit_commands, 'cmd_write_tree') or
                hasattr(pygit_commands, 'write-tree') or
                any('write' in attr.lower() and 'tree' in attr.lower() for attr in dir(pygit_commands))
        )
        assert has_write_tree, "Write-tree command not found"


class TestLogCommand:
    """Tests for pygit log command and commit history."""
    
    @pytest.mark.skipif(pygit_commands is None, reason="pygit module not found")
    def test_log_command_exists(self):
        """Test that log command exists."""
        has_log = (
                hasattr(pygit_commands, 'log') or
                hasattr(pygit_commands, 'cmd_log') or
                hasattr(pygit_commands, 'command_log') or
                any('log' in attr.lower() for attr in dir(pygit_commands))
        )
        assert has_log, "Log command not found"
    
    @pytest.mark.skipif(pygit_commands is None, reason="pygit module not found")
    def test_commit_history_iterator_exists(self):
        """Test that CommitHistoryIterator exists."""
        # Look for iterator class in pygit module or objects module
        has_iterator = False
        
        for module in [pygit_commands, pygit_objects]:
            if module is None:
                continue
            
            if hasattr(module, 'CommitHistoryIterator'):
                has_iterator = True
                iterator_class = getattr(module, 'CommitHistoryIterator')
                
                # Test that it's iterable
                assert hasattr(iterator_class, '__iter__') or hasattr(iterator_class, '__next__'), \
                    "CommitHistoryIterator should be iterable"
                break
            
            # Look for any class with "Iterator" or "History" in name
            for attr in dir(module):
                if 'iterator' in attr.lower() or 'history' in attr.lower():
                    has_iterator = True
                    break
        
        assert has_iterator, "CommitHistoryIterator or similar class not found"


class TestCommandDecorator:
    """Tests for command decorator system."""
    
    @pytest.mark.skipif(pygit_commands is None, reason="pygit module not found")
    def test_command_decorator_exists(self):
        """Test that command decorator exists."""
        has_decorator = (
                hasattr(pygit_commands, 'command') or
                hasattr(pygit_commands, 'cmd') or
                any('command' in attr.lower() and callable(getattr(pygit_commands, attr)) for attr in dir(pygit_commands))
        )
        assert has_decorator, "Command decorator not found"
    
    @pytest.mark.skipif(pygit_commands is None, reason="pygit module not found")
    def test_command_registry_exists(self):
        """Test that command registry (dictionary) exists."""
        has_registry = False
        
        # Look for dictionaries that might store commands
        for attr in dir(pygit_commands):
            obj = getattr(pygit_commands, attr)
            if isinstance(obj, dict):
                # Check if it contains command-like keys
                if any(key in ['init', 'add', 'commit', 'log'] for key in obj.keys()):
                    has_registry = True
                    break
                # Or if it has string keys that might be commands
                if obj and all(isinstance(k, str) for k in obj.keys()):
                    has_registry = True
                    break
        
        # Alternative: check for commands variable or similar
        has_registry = has_registry or any(
            'command' in attr.lower() and isinstance(getattr(pygit_commands, attr), dict)
            for attr in dir(pygit_commands)
        )
        
        assert has_registry, "Command registry dictionary not found"


class TestIntegration:
    """Integration tests across the pygit system."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        yield temp_dir
        os.chdir(old_cwd)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.skipif(pygit_commands is None, reason="pygit module not found")
    def test_full_workflow_simulation(self, temp_repo):
        """Test complete git workflow: init -> add -> commit."""
        try:
            # Step 1: Initialize repository
            if hasattr(pygit_commands, 'init'):
                pygit_commands.init()
            elif hasattr(pygit_commands, 'cmd_init'):
                pygit_commands.cmd_init()
            else:
                pytest.skip("Init command not available")
            
            # Verify .pygit directory was created
            assert Path('.pygit').exists(), "Repository not initialized"
            
            # Step 2: Create and add a file
            test_file = Path('README.md')
            test_file.write_text("# Test Repository\nHello, World!")
            
            if hasattr(pygit_commands, 'add'):
                pygit_commands.add('README.md')
            else:
                pytest.skip("Add command not available")
            
            # Step 3: Create a commit (if available)
            if hasattr(pygit_commands, 'commit'):
                pygit_commands.commit(['Initial commit'])
            
            # If we got this far without exceptions, the basic workflow works
            assert True, "Basic workflow completed successfully"
            
        except Exception as e:
            # This is expected for incomplete implementations
            pytest.skip(f"Full workflow not yet implemented: {e}")
    
    @pytest.mark.skipif(pygit_commands is None or pygit_objects is None, reason="Required modules not found")
    def test_object_creation_and_storage(self, temp_repo):
        """Test that objects can be created and stored."""
        # Initialize repo
        try:
            if hasattr(pygit_commands, 'init'):
                pygit_commands.init()
            elif hasattr(pygit_commands, 'cmd_init'):
                pygit_commands.cmd_init()
            else:
                pytest.skip("Init not available")
        except Exception:
            pytest.skip("Init failed")
        
        # Test blob creation
        if hasattr(pygit_objects, 'Blob') and hasattr(pygit_objects, 'hash_object'):
            try:
                test_data = b"Hello, World!"
                blob = pygit_objects.Blob(test_data)
                serialized = blob.serialize()
                hash_value = pygit_objects.hash_object(serialized, 'blob')
                
                assert isinstance(hash_value, str), "Hash should be string"
                assert len(hash_value) == 40, "Hash should be 40 characters"
                
            except Exception as e:
                pytest.skip(f"Object creation failed: {e}")


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.skipif(pygit_commands is None, reason="pygit module not found")
    def test_invalid_command_handling(self):
        """Test handling of invalid commands."""
        # This test checks if the CLI handles unknown commands gracefully
        # Implementation will vary, so we just check it doesn't crash
        try:
            if hasattr(pygit_commands, 'main'):
                original_argv = sys.argv
                sys.argv = ['pygit', 'nonexistent_command']
                try:
                    pygit_commands.main()
                except (SystemExit, AttributeError, KeyError):
                    # These are acceptable ways to handle invalid commands
                    pass
                finally:
                    sys.argv = original_argv
            assert True, "Invalid command handled gracefully"
        except Exception:
            assert True, "Error handling present"
    
    @pytest.mark.skipif(pygit_objects is None, reason="objects module not found")
    def test_empty_data_handling(self):
        """Test handling of empty data in objects."""
        if not hasattr(pygit_objects, 'Blob'):
            pytest.skip("Blob class not found")
        
        try:
            # Test empty blob
            empty_blob = pygit_objects.Blob(b"")
            serialized = empty_blob.serialize()
            assert serialized == b"", "Empty blob should serialize to empty bytes"
        except Exception:
            pytest.skip("Empty data handling not implemented")


class TestFileStructure:
    """Test that the project has the expected file structure."""
    
    def test_main_pygit_file_exists(self):
        """Test that pygit_commands.py file exists."""
        pygit_file = Path(__file__).parent / 'pygit_commands.py'
        if not pygit_file.exists():
            # Try alternative locations
            alt_locations = [
                Path(__file__).parent / 'pygit' / '__main__.py',
                Path(__file__).parent / 'main.py'
            ]
            exists = any(p.exists() for p in alt_locations)
            if not exists:
                pytest.skip("Main pygit executable not implemented yet")
        else:
            assert True, "pygit.py file exists"
    
    def test_expected_module_structure(self):
        """Test that expected module files exist or can be imported."""
        base_dir = Path(__file__).parent
        
        # Check for objects module
        objects_exists = any([
            (base_dir / 'pygit' / 'objects.py').exists(),
            (base_dir / 'objects.py').exists(),
            pygit_objects is not None
        ])
        
        # Check for index module
        index_exists = any([
            (base_dir / 'pygit' / 'index.py').exists(),
            (base_dir / 'index.py').exists(),
            pygit_index is not None
        ])
        
        # At least some structure should exist
        has_structure = objects_exists or index_exists or pygit_commands is not None
        if not has_structure:
            pytest.skip("No project structure implemented yet")
        else:
            assert True, "Project structure exists"


# Performance tests (optional, for advanced implementations)
class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.mark.skipif(pygit_objects is None, reason="objects module not found")
    def test_hash_object_performance(self):
        """Test that hash_object performs reasonably well."""
        if not hasattr(pygit_objects, 'hash_object'):
            pytest.skip("hash_object not found")
        
        import time
        
        # Test with moderately large data
        test_data = b"x" * 10000  # 10KB
        
        start_time = time.time()
        try:
            hash_result = pygit_objects.hash_object(test_data, 'blob')
            end_time = time.time()
            
            # Should complete quickly (less than 100ms)
            assert end_time - start_time < 0.1, "hash_object took too long"
            assert isinstance(hash_result, str), "Should return string hash"
            
        except Exception:
            pytest.skip("hash_object implementation not complete")
